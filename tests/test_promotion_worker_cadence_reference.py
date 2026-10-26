"""Explicit finite synthetic autobump proof with restricted prefork and native Beat60."""

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redis
from capacity_runtime_role import _owned_database, runtime_role_environment
from celery.signals import before_task_publish
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_listing_start_queued_baseline import identity_gone, read_events
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_worker_capacity_comparison import process_tree, terminate_owned, wait_for_log

from apps.catalog.promotion_order_models import PromotionBumpExecution, PromotionEntitlement
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Person
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
BUMP = 'apps.catalog.tasks.bump_promotions'
REFRESH = 'apps.listings.tasks.refresh_publication_state'
ALLOWED = {BUMP, REFRESH}
NATIVE_ENTRY = 'synthetic-promotion-bumps'


def test_promotion_native_worker_and_two_beat_ticks(
    request, settings, tmp_path, monkeypatch, record_property
):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit owned serial synthetic promotion cadence diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert request.config.pluginmanager.hasplugin('scripts.local_ci_broker')
    generation = request.getfixturevalue('isolated_test_broker')
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{8}', run)
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert generation == os.environ['LOCAL_CI_TEST_QUEUE_GENERATION'] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == 'local' and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    endpoint = urlsplit(settings.CELERY_BROKER_URL)
    assert endpoint.hostname == '127.0.0.1' and endpoint.path == '/0' and endpoint.port
    assert settings.CELERY_BROKER_TRANSPORT_OPTIONS['global_keyprefix'] == f'clasificados:{generation}:'
    broker = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    prefix = f'clasificados:{generation}:'.encode()
    assert not list(broker.scan_iter(match=prefix + b'*'))
    foreign = {key: hashlib.sha256(broker.dump(key)).hexdigest()
               for key in broker.scan_iter() if broker.exists(key)}

    # All native fixture and signed synthetic purchase work is outside task clocks.
    user, first_listing, version, credentials = setup(request, settings)
    assert celery_app.conf.task_always_eager
    version.product.kind = 'autobump'
    version.product.save(update_fields=['kind'])
    version.bump_interval_minutes, version.daily_bump_limit = 1440, 1
    version.save(update_fields=['bump_interval_minutes', 'daily_bump_limit'])
    agency_person = Person.objects.select_related('agency__owner').get(
        subject__username='fixture-v1-model-a'
    )
    assert agency_person.agency_id and agency_person.pk != first_listing.person_id
    agency_user = agency_person.agency.owner
    agency_user.mfa_enabled = True
    agency_user.save(update_fields=['mfa_enabled'])
    second_listing = agency_person.listing
    assert publicly_visible(first_listing) and publicly_visible(second_listing)
    auth = {'mfa_version': agency_user.mfa_version,
            'account_version': agency_user.session_version}
    orders = [create_order(user, first_listing.pk, version.pk, uuid.uuid4(), **credentials),
              create_order(agency_user, second_listing.pk, version.pk, uuid.uuid4(), **auth)]
    for order, buyer, values in zip(orders, (user, agency_user), (credentials, auth)):
        payload, signature = synthetic_event(order.payment_attempt, 'succeeded', uuid.uuid4())
        receive_event(buyer, payload, signature, **values)
        order.refresh_from_db()
        assert order.synthetic and order.status == 'paid'
        assert order.kind == 'autobump' and order.duration_days == 10
        assert order.bump_interval_minutes == 1440 and order.daily_bump_limit == 1
    first, second = [order.entitlement for order in orders]
    now = timezone.now()
    first.starts_at = now - timedelta(days=2)
    first.ends_at = first.starts_at + timedelta(days=10)
    second.starts_at = now + timedelta(days=1)
    second.ends_at = second.starts_at + timedelta(days=10)
    for entitlement in (first, second):
        entitlement.save(update_fields=['starts_at', 'ends_at'])
        assert entitlement.ends_at - entitlement.starts_at == timedelta(days=10)
    assert PromotionEntitlement.objects.count() == 2
    assert not PromotionBumpExecution.objects.exists()
    listing_ids = [first_listing.pk, second_listing.pk]

    def editorial():
        return {str(row.pk): {'published_at': row.published_at.isoformat(),
                             'expires_at': row.expires_at.isoformat(),
                             'lifecycle_version': row.lifecycle_version,
                             'approved_revision_id': str(row.approved_revision_id),
                             'revision_count': row.revisions.count(), 'status': row.status}
                for row in Listing.objects.filter(pk__in=listing_ids)}

    baseline_editorial = editorial()
    out = Path(request.config.getoption('--gate-timings-output')).parent
    events = out / 'n08c-promotion-events'
    events.mkdir()
    work = tmp_path / 'n08c-private-runtime'
    work.mkdir(mode=0o700)
    module = 'n08c_promotion_settings'
    # Enable source configuration before importing config.settings in child processes.
    monkeypatch.setenv('PROMOTION_TEST_MODE', '1')
    (work / (module + '.py')).write_text(
        'import os\nos.environ["PROMOTION_TEST_MODE"] = "1"\n'
        'from local_ci_settings import *\nfrom pathlib import Path\n'
        + f'MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n'
        + f'RIGHTS_DELIVERY_ROOT = Path({str(work / "delivery")!r})\n'
        + 'assert PROMOTION_TEST_MODE and not PRODUCTION and not RECOVERY_MODE\n'
        + f'_entry = dict(CELERY_BEAT_SCHEDULE[{NATIVE_ENTRY!r}])\n'
        + f'assert _entry["task"] == {BUMP!r} and _entry["schedule"] == 60.0\n'
        + f'CELERY_BEAT_SCHEDULE = {{{NATIVE_ENTRY!r}: _entry}}\n'
        + 'CELERY_TASK_ALWAYS_EAGER = False\nCELERY_TASK_EAGER_PROPAGATES = False\n'
        + 'CELERY_RESULT_EXPIRES = None\n'
        + 'import scripts.benchmark_celery_observer as _observer\n'
        + 'from celery.signals import task_prerun, task_postrun\n'
        + '@task_prerun.connect(weak=False)\n'
        + 'def _epoch_proof(task_id=None, task=None, **kwargs):\n'
        + '    import time\n'
        + '    _observer._write({"event":"task_epoch", "id":task_id, "task":task.name, "epoch":time.time()})\n'
        + '@task_postrun.connect(weak=False)\n'
        + 'def _role_proof(task_id=None, task=None, **kwargs):\n'
        + '    from django.db import connection\n'
        + '    from apps.catalog.promotion_order_models import PromotionEntitlement\n'
        + '    with connection.cursor() as cursor:\n'
        + '        cursor.execute("SELECT current_user, extract(epoch from clock_timestamp())")\n'
        + '        role, epoch = cursor.fetchone()\n'
        + f'    rows = PromotionEntitlement.objects.filter(pk__in={[str(first.pk), str(second.pk)]!r})\n'
        + '    checked = {str(row.pk): row.last_checked_at.timestamp() if row.last_checked_at else None for row in rows}\n'
        + '    _observer._write({"event":"role_proof", "id":task_id, "task":task.name, "pid":os.getpid(), "sql_role":role, "end_epoch":float(epoch), "last_checked_epochs":checked})\n'
    )
    (work / (module + '.py')).chmod(0o600)
    monkeypatch.setenv('PYTHONPATH', str(work) + os.pathsep + os.environ.get('PYTHONPATH', ''))
    worker = beat = None
    identities, publishes = {}, []
    role = private_path = None
    report = {'complete': False, 'scope': 'Two signed synthetic purchases; restricted prefork2; two unchanged60s Beat ticks. No provider, production capacity or improvement claim.',
              'schedule': {'source': 'config/settings.py', 'entry': NATIVE_ENTRY, 'seconds': 60.0},
              'measurement_note': 'Startup includes prequeued task and worker startup; steady replay and Beat executions separate. Setup/assertions and private postrun role/snapshot proof excluded from observer task wall; observer overhead included.',
              'phases': {}, 'editorial_before': baseline_editorial}

    def capture(sender=None, headers=None, **kwargs):
        publishes.append({'event': 'publish', 'task': sender, 'id': (headers or {}).get('id'),
                          'role': 'harness', 'monotonic': time.monotonic(), 'epoch': time.time()})

    def track(child):
        if child is None:
            return
        for pid in process_tree(child.pid):
            try:
                ticks = int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19])
            except FileNotFoundError:
                continue
            assert pid not in identities or identities[pid] == ticks
            identities[pid] = ticks

    def rows():
        data = read_events(events)
        assert len(data) <= 2000 and not any('snapshot_error' in row for row in data)
        assert all(row['task'] in ALLOWED for row in data)
        return data

    def wait(predicate, seconds, label, require_beat=False):
        deadline = time.monotonic() + seconds
        while True:
            assert worker is not None and worker.poll() is None
            track(worker)
            if require_beat:
                assert beat is not None and beat.poll() is None
            if beat is not None and beat.poll() is None:
                track(beat)
            data = rows()
            if predicate(data):
                return data
            assert time.monotonic() < deadline, label
            time.sleep(.05)

    def drained(data):
        sent = publishes + [row for row in data if row['event'] == 'publish']
        assert all(row['task'] in ALLOWED for row in sent)
        executions = [row for row in data if row['event'] == 'execution']
        proofs = {row['id']: row for row in data if row['event'] == 'role_proof'}
        epochs = {row['id'] for row in data if row['event'] == 'task_epoch'}
        assert len({row['id'] for row in executions}) == len(executions)
        for row in executions:
            assert row['state'] == 'SUCCESS' and row['eager'] is False
            assert row['pid'] in identities and row['pid'] != worker.pid
            if row['id'] in proofs:
                assert proofs[row['id']]['sql_role'] == role
                assert proofs[row['id']]['pid'] == row['pid']
        sent_ids = {row['id'] for row in sent}
        return sent_ids <= {row['id'] for row in executions} and sent_ids <= proofs.keys() and sent_ids <= epochs

    def drain():
        return wait(drained, 45, 'Owned promotion queue drain expired')

    def execution(data, task_id):
        return next(row for row in data if row['event'] == 'execution' and row['id'] == task_id)

    def windows(entitlement):
        return list(PromotionBumpExecution.objects.filter(entitlement=entitlement)
                    .order_by('window_start').values_list('window_start', flat=True))

    before_task_publish.connect(capture, weak=False)
    try:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=False):
            assert celery_app.conf.task_always_eager is False
            with runtime_role_environment(module) as runtime:
                role = runtime['POSTGRES_USER']
                private_path = Path(runtime['RIGHTS_EVIDENCE_RUNTIME_CONFIG'])
                report['runtime_role'] = role
                env = {**os.environ, **runtime, 'POSTGRES_DB': connection.settings_dict['NAME'],
                       'PROMOTION_TEST_MODE': '1', 'WEB_MODELOS_CELERY_OBSERVER_DIR': str(events),
                       'WEB_MODELOS_PROCESS_ROLE': 'worker'}
                try:
                    started = time.monotonic()
                    first_job = celery_app.send_task(BUMP).id
                    assert len(publishes) == 1 and publishes[0]['id'] == first_job
                    report['phases']['startup'] = {'queued_before_worker': True, 'publish': publishes[0],
                                                  'started_monotonic': started}
                    assert not windows(first) and not windows(second)
                    log = out / 'n08c-worker.log'
                    with log.open('w') as stream:
                        worker = subprocess.Popen([sys.executable, '-m', 'celery', '-A', 'config', 'worker',
                                                   '--loglevel=INFO', '--pool=prefork', '--concurrency=2'],
                                                  env=env, stdout=stream, stderr=stream, start_new_session=True)
                    track(worker)
                    wait_for_log(log, ' ready.', worker, time.monotonic() + 45)
                    track(worker)
                    assert len(identities) >= 3
                    data = drain()
                    first_execution = execution(data, first_job)
                    assert first_execution['result'] == 1 and len(windows(first)) == 1
                    assert not windows(second) and editorial() == baseline_editorial
                    report['phases']['startup'].update(
                        execution=first_execution,
                        publish_to_start_seconds=first_execution['start_monotonic'] - publishes[0]['monotonic'],
                        observed_complete_seconds=time.monotonic() - started,
                        first_windows=[value.isoformat() for value in windows(first)],
                        second_future_has_zero_bumps=True)

                    before_windows = windows(first)
                    replay_job = celery_app.send_task(BUMP).id
                    data = drain()
                    replay_execution = execution(data, replay_job)
                    after_windows = windows(first)
                    assert set(before_windows) <= set(after_windows)
                    assert len(after_windows) == len(set(after_windows))
                    assert len({value.astimezone(UTC).date() for value in after_windows}) == len(after_windows)
                    assert all(value == value.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
                               for value in after_windows)
                    new_windows = set(after_windows) - set(before_windows)
                    assert len(new_windows) in (0, 1) and replay_execution['result'] == len(new_windows)
                    epoch = next(row['epoch'] for row in data if row['event'] == 'task_epoch' and row['id'] == replay_job)
                    proof = next(row for row in data if row['event'] == 'role_proof' and row['id'] == replay_job)
                    days = {datetime.fromtimestamp(value, UTC).date() for value in (epoch, proof['end_epoch'])}
                    if new_windows:
                        assert all(value.date() in days for value in new_windows)
                    else:
                        assert any(value.date() in days for value in before_windows)
                    assert not windows(second) and editorial() == baseline_editorial
                    publication = next(row for row in publishes if row['id'] == replay_job)
                    report['phases']['live_replay'] = {
                        'publish': publication, 'execution': replay_execution,
                        'publish_to_start_seconds': replay_execution['start_monotonic'] - publication['monotonic'],
                        'windows_before': [value.isoformat() for value in before_windows],
                        'windows_after': [value.isoformat() for value in after_windows],
                        'new_utc_day_window': bool(new_windows), 'task_start_epoch': epoch,
                        'postrun_db_epoch': proof['end_epoch'], 'quota_one_per_utc_day': True}

                    # Exclude first by suspension; second is selected but freshly ineligible.
                    first.suspended_at = timezone.now()
                    first.save(update_fields=['suspended_at'])
                    active = timezone.now()
                    second.starts_at = active - timedelta(days=2)
                    second.ends_at = second.starts_at + timedelta(days=10)
                    second.save(update_fields=['starts_at', 'ends_at'])
                    agency_person.consent_revoked_at = timezone.now()
                    agency_person.save(update_fields=['consent_revoked_at'])
                    assert not publicly_visible(Listing.objects.get(pk=second_listing.pk))
                    data = drain()  # Account for every native REFRESH; not bump work.
                    assert not windows(second)
                    assert windows(first) == after_windows
                    assert editorial() == baseline_editorial
                    second.refresh_from_db()
                    assert second.last_checked_at is None
                    beat_start = time.monotonic()
                    report['phases']['native_beat'] = {'started_monotonic': beat_start,
                        'revoked_before_beat': agency_person.consent_revoked_at.isoformat(),
                        'first_excluded_by_suspension': True, 'second_selected_but_revoked': True}
                    with (out / 'n08c-beat.log').open('w') as stream:
                        beat = subprocess.Popen([sys.executable, '-m', 'celery', '-A', 'config', 'beat',
                                                 '--loglevel=INFO', '--schedule', str(work / 'beat-schedule')],
                                                env=dict(env, WEB_MODELOS_PROCESS_ROLE='beat'),
                                                stdout=stream, stderr=stream, start_new_session=True)
                    track(beat)

                    def two_ticks_done(data):
                        ticks = [row for row in data if row['event'] == 'publish' and row['role'] == 'beat']
                        assert all(row['task'] == BUMP for row in ticks)
                        if len(ticks) < 2 or not drained(data):
                            return False
                        return True

                    wait(two_ticks_done, 180, 'Native60s promotion Beat two ticks expired', require_beat=True)
                    terminate_owned(beat)
                    data = drain()
                    ticks = sorted([row for row in data if row['event'] == 'publish' and row['role'] == 'beat'],
                                   key=lambda row: row['monotonic'])
                    assert len(ticks) == 2
                    proofs = {row['id']: row for row in data if row['event'] == 'role_proof'}
                    ledger, checked = [], []
                    for tick in ticks:
                        row = execution(data, tick['id'])
                        assert row['result'] == 0
                        value = proofs[tick['id']]['last_checked_epochs'][str(second.pk)]
                        assert value is not None and value >= active.timestamp()
                        checked.append(value)
                        ledger.append({'publish': tick, 'execution': row,
                                       'publish_to_start_seconds': row['start_monotonic'] - tick['monotonic'],
                                       'second_last_checked_epoch': value})
                    assert checked[1] > checked[0]
                    assert ticks[1]['monotonic'] > ticks[0]['monotonic']
                    second.refresh_from_db()
                    assert second.last_checked_at.timestamp() == checked[-1]
                    assert not windows(second) and windows(first) == after_windows
                    assert editorial() == baseline_editorial
                    report['phases']['native_beat'].update(
                        ticks=ledger,
                        tick_separation_seconds=ticks[1]['monotonic'] - ticks[0]['monotonic'],
                        second_zero_bumps=True, last_checked_advanced_each_tick=True)
                    report['editorial_after'] = editorial()
                    report['executor_pids'] = sorted({row['pid'] for row in data if row['event'] == 'execution'})
                    report['complete'] = True
                finally:
                    errors = []
                    for child in (beat, worker):
                        try:
                            track(child)
                            terminate_owned(child)
                        except Exception as exc:
                            errors.append(type(exc).__name__)
                    deadline = time.monotonic() + 5
                    while True:
                        absent = {str(pid): identity_gone(pid, ticks) for pid, ticks in identities.items()}
                        if all(absent.values()) or time.monotonic() >= deadline:
                            break
                        time.sleep(.05)
                    report.update(pid_start_ticks=identities, processes_absent=absent, cleanup_errors=errors,
                                  worker_exit_code=None if worker is None else worker.poll(),
                                  beat_exit_code=None if beat is None else beat.poll())
                    assert all(absent.values()) and not errors
                    assert worker is None or worker.poll() is not None
                    assert beat is None or beat.poll() is not None
    finally:
        before_task_publish.disconnect(capture)
        report['harness_publishes'] = publishes
        report['namespace_generation'] = generation
        if sys.exc_info()[0] is not None:
            report['failure_type'] = sys.exc_info()[0].__name__
            report['complete'] = False
        try:
            if role is not None:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)', [role])
                    report['runtime_role_removed'] = cursor.fetchone()[0]
            if private_path is not None:
                report['private_credentials_removed'] = not private_path.exists()
        except Exception as exc:
            report['role_cleanup_snapshot_error'] = type(exc).__name__
        try:
            remaining = set(broker.scan_iter())
            report['foreign_keys_preserved'] = set(foreign) <= remaining and all(
                hashlib.sha256(broker.dump(key)).hexdigest() == digest for key, digest in foreign.items())
            report['unexpected_unscoped_keys'] = sum(not key.startswith(prefix) for key in remaining - foreign.keys())
            report['events'] = rows()
        except Exception as exc:
            report['final_snapshot_error'] = type(exc).__name__
        try:
            if all(identity_gone(pid, ticks) for pid, ticks in identities.items()):
                shutil.rmtree(work)
        except Exception as exc:
            report['private_runtime_cleanup_error'] = type(exc).__name__
        report['private_runtime_removed'] = not work.exists()
        report['complete'] = bool(
            report['complete'] and report.get('foreign_keys_preserved')
            and report.get('unexpected_unscoped_keys') == 0
            and report.get('runtime_role_removed') and report.get('private_credentials_removed')
            and report['private_runtime_removed']
            and not any(key in report for key in (
                'failure_type', 'final_snapshot_error', 'role_cleanup_snapshot_error',
                'private_runtime_cleanup_error',
            ))
        )
        (out / 'n08c-promotion-runtime.json').write_text(json.dumps(report, allow_nan=False, indent=2) + '\n')
        record_property('n08c_promotion_cadence', json.dumps(report, allow_nan=False, sort_keys=True))
    assert report['complete'] and report['foreign_keys_preserved'] and report['unexpected_unscoped_keys'] == 0
    assert 'failure_type' not in report and 'final_snapshot_error' not in report
    assert 'role_cleanup_snapshot_error' not in report
    assert report['private_runtime_removed'] and report['runtime_role_removed'] and report['private_credentials_removed']
    assert report['worker_exit_code'] == 0 and report['beat_exit_code'] in (0, -15)
    for row in report['events']:
        for field in ('monotonic', 'start_monotonic', 'end_monotonic', 'wall', 'thread_cpu', 'db_wall', 'epoch', 'end_epoch'):
            if field in row:
                assert isinstance(row[field], (float, int)) and math.isfinite(row[field]) and row[field] >= 0
