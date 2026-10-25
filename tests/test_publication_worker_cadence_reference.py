"""Finite explicit owned worker/Beat observation; synthetic preparation is eager."""

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
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redis
from capacity_runtime_role import _owned_database, runtime_role_environment
from celery.signals import before_task_publish
from django.db import connection
from django.test import Client, override_settings
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_listing_start_queued_baseline import identity_gone, read_events
from test_photos import photo_environment  # noqa: F401
from test_worker_capacity_comparison import process_tree, terminate_owned, wait_for_log

from apps.core.models import Person, User
from apps.listings import publication_state
from apps.listings.models import LifecycleAction, Listing, PublicationDirty, PublicationState
from apps.listings.publication_state import (
    STATE_COLUMNS,
    expected_states,
    refresh_all,
    rules_version,
)
from config.celery import app as celery_app
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)
REFRESH = 'apps.listings.tasks.refresh_publication_state'
EXPIRE = 'apps.listings.tasks.expire_listings'
SWEEP = 'apps.listings.tasks.sweep_publication_state'
ALLOWED = {REFRESH, EXPIRE, SWEEP}


def test_publication_native_worker_and_beat(request, settings, tmp_path, monkeypatch, record_property):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit owned serial publication cadence diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert request.config.pluginmanager.hasplugin('scripts.local_ci_broker')
    generation = request.getfixturevalue('isolated_test_broker')
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{8}', run)
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert generation == os.environ['LOCAL_CI_TEST_QUEUE_GENERATION'] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert not publication_state.READ_REPAIR, 'This reference requires native default read repair disabled'
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == 'local' and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    endpoint = urlsplit(settings.CELERY_BROKER_URL)
    assert endpoint.hostname == '127.0.0.1' and endpoint.path == '/0' and endpoint.port
    schedules = {'refresh-publication-state': (REFRESH, 30.0),
                 'expire-public-listings': (EXPIRE, 60.0)}
    for name, (task, seconds) in schedules.items():
        assert settings.CELERY_BEAT_SCHEDULE[name]['task'] == task
        assert settings.CELERY_BEAT_SCHEDULE[name]['schedule'] == seconds
    broker = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    prefix = f'clasificados:{generation}:'.encode()
    assert not list(broker.scan_iter(match=prefix + b'*'))
    foreign = {key: hashlib.sha256(broker.dump(key)).hexdigest()
               for key in broker.scan_iter() if broker.exists(key)}
    # Native seed and synthetic cloning, including direct refresh, precede measurement.
    request.getfixturevalue('directory')
    assert celery_app.conf.task_always_eager
    dataset = populate(100)
    refresh_all()
    assert not PublicationDirty.objects.exists()
    person = Person.objects.get(individual__username='fixture-v1-individual')
    individual = person.listing
    others = list(Listing.objects.filter(status='published').exclude(pk=individual.pk).order_by('pk')[:4])
    assert len(others) == 4
    bulk, raw, overdue, corrupt = others
    manager, visitor = Client(), Client()
    manager.force_login(person.individual)
    visitor.force_login(User.objects.get(username='fixture-v1-visitor'))
    assert visitor.post(f'/en/listing/{individual.pk}/favorite/').status_code == 302
    out = Path(request.config.getoption('--gate-timings-output')).parent
    events = out / 'n07b-publication-events'
    events.mkdir()
    work = tmp_path / 'n07b-private-runtime'
    work.mkdir(mode=0o700)
    module = 'n07b_publication_settings'
    # A local extra signal observes current_user in each actual child execution;
    # benchmark_celery_observer remains unchanged and supplies timings/dirty ages.
    (work / (module + '.py')).write_text(
        'from local_ci_settings import *\nfrom pathlib import Path\n'
        + f'MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n'
        + f'RIGHTS_DELIVERY_ROOT = Path({str(work / "delivery")!r})\n'
        + 'CELERY_TASK_ALWAYS_EAGER = False\nCELERY_TASK_EAGER_PROPAGATES = False\n'
        + 'CELERY_RESULT_EXPIRES = None\n'
        + f'CELERY_BEAT_SCHEDULE = {{k: dict(CELERY_BEAT_SCHEDULE[k]) for k in {list(schedules)!r}}}\n'
        + 'import scripts.benchmark_celery_observer as _observer\n'
        + 'from celery.signals import task_postrun\n'
        + '@task_postrun.connect(weak=False)\n'
        + 'def _role_proof(task_id=None, task=None, **kwargs):\n'
        + '    from django.db import connection\n'
        + '    import os\n'
        + '    with connection.cursor() as cursor:\n'
        + '        cursor.execute("SELECT current_user")\n'
        + '        role = cursor.fetchone()[0]\n'
        + '    _observer._write({"event":"role_proof", "id":task_id, "task":task.name, "pid":os.getpid(), "sql_role":role})\n'
    )
    (work / (module + '.py')).chmod(0o600)
    monkeypatch.setenv('PYTHONPATH', str(work) + os.pathsep + os.environ.get('PYTHONPATH', ''))
    worker = beat = None
    identities, publishes = {}, []
    role = private_path = None
    report = {'complete': False, 'dataset': dataset, 'phases': {},
              'scope': 'Synthetic100; native restricted prefork2 and unchanged30/60s Beat subset. No provider, SLA, capacity or hourly cadence claim.',
              'measurement_note': 'Phase A includes queued worker startup. Phase B starts with a live drained worker. Setup eager/direct refresh and native equality oracle are outside measured task intervals. Observer SQL/bookkeeping overhead included.'}

    def capture(sender=None, headers=None, **kwargs):
        publishes.append({'event': 'publish', 'task': sender, 'id': (headers or {}).get('id'),
                          'role': 'harness', 'monotonic': time.monotonic()})

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

    def wait(predicate, seconds, label):
        deadline = time.monotonic() + seconds
        while True:
            assert worker is not None and worker.poll() is None
            track(worker)
            if beat is not None and beat.poll() is None:
                track(beat)
            data = rows()
            if predicate(data):
                return data
            assert time.monotonic() < deadline, label
            time.sleep(.05)

    def drain():
        def done(data):
            sent = publishes + [r for r in data if r['event'] == 'publish']
            assert all(r['task'] in ALLOWED for r in sent)
            executions = [r for r in data if r['event'] == 'execution']
            proofs = {r['id']: r for r in data if r['event'] == 'role_proof'}
            assert len({r['id'] for r in executions}) == len(executions)
            for row in executions:
                assert row['state'] == 'SUCCESS' and row['eager'] is False
                assert row['pid'] in identities and row['pid'] != worker.pid
                if row['id'] in proofs:
                    assert proofs[row['id']]['sql_role'] == role
                    assert proofs[row['id']]['pid'] == row['pid']
            ids = {r['id'] for r in sent}
            return ids <= {r['id'] for r in executions} and ids <= proofs.keys()
        return wait(done, 45, 'Owned publication queue drain expired')

    def dirty():
        with connection.cursor() as cursor:
            cursor.execute('SELECT count(*), COALESCE(max(extract(epoch FROM clock_timestamp()-marked_at)),0) FROM listings_publicationdirty')
            count, age = cursor.fetchone()
        return {'count': count, 'oldest_age_seconds': float(age), 'monotonic': time.monotonic()}

    def deny(listing):
        photo = listing.approved_revision.photos.first()
        assert photo
        assert Client().get(f'/en/listing/{listing.pk}/').status_code == 404
        assert Client().get(f'/en/listing/{listing.pk}/photo/{photo.pk}/').status_code == 404
        assert visitor.post(f'/en/listing/{listing.pk}/favorite/').status_code == 404

    def public_pages(expected_count, denied):
        observed = []
        for language in ('es', 'en'):
            found = []
            pages = max(1, math.ceil(expected_count / 24))
            for number in range(1, pages + 1):
                response = Client().get(f'/{language}/', {'page': number})
                assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                page = response.context['page']
                assert page.paginator.count == expected_count
                assert page.paginator.num_pages == pages
                found.extend(row.pk for row in page.object_list)
            assert len(found) == len(set(found)) == expected_count
            assert not set(denied).intersection(found)
            observed.append({'language': language, 'pages': pages,
                             'count': expected_count, 'unique': len(set(found)), 'denied_absent': True})
        return observed

    def equality():
        ids = list(Listing.objects.values_list('pk', flat=True))
        expected = expected_states(ids, rules_version())
        stored = {s.listing_id: s for s in PublicationState.objects.all()}
        assert set(stored) == set(expected)
        assert all(all(getattr(stored[key], col) == getattr(value, col) for col in STATE_COLUMNS)
                   for key, value in expected.items())
        assert not PublicationDirty.objects.exists()
        return {'rows': len(expected), 'columns': list(STATE_COLUMNS), 'equal': True}

    before_task_publish.connect(capture, weak=False)
    try:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=False):
            assert celery_app.conf.task_always_eager is False
            with runtime_role_environment(module) as runtime:
                role = runtime['POSTGRES_USER']
                private_path = Path(runtime['RIGHTS_EVIDENCE_RUNTIME_CONFIG'])
                report['runtime_role'] = role
                env = {**os.environ, **runtime, 'POSTGRES_DB': connection.settings_dict['NAME'],
                       'WEB_MODELOS_CELERY_OBSERVER_DIR': str(events), 'WEB_MODELOS_PROCESS_ROLE': 'worker'}
                try:
                    started = time.monotonic()
                    assert manager.post(f'/en/listing/{individual.pk}/manage/', {
                        'key': str(uuid.uuid4()), 'version': individual.lifecycle_version,
                        'operation': 'pause'}).status_code == 302
                    assert len(publishes) == 1 and publishes[0]['task'] == REFRESH
                    assert PublicationDirty.objects.filter(listing_id=individual.pk).exists()
                    deny(individual)
                    startup_public = public_pages(99, [individual.pk])
                    assert PublicationDirty.objects.filter(listing_id=individual.pk).exists()
                    favorite_page = visitor.get('/en/favorites/')
                    assert b'Listing unavailable' in favorite_page.content
                    assert str(individual.pk).encode() not in favorite_page.content
                    backlog = dirty()
                    assert backlog['count'] >= 1
                    log = out / 'n07b-worker.log'
                    with log.open('w') as stream:
                        worker = subprocess.Popen([sys.executable, '-m', 'celery', '-A', 'config', 'worker',
                                                   '--loglevel=INFO', '--pool=prefork', '--concurrency=2'],
                                                  env=env, stdout=stream, stderr=stream, start_new_session=True)
                    track(worker)
                    wait_for_log(log, ' ready.', worker, time.monotonic() + 45)
                    track(worker)
                    assert len(identities) >= 3
                    data = drain()
                    execution = next(r for r in data if r['event'] == 'execution' and r['id'] == publishes[0]['id'])
                    report['phases']['startup_backlog'] = {
                        'start_monotonic': started, 'backlog': backlog, 'publish': publishes[0],
                        'public_pages_before_worker': startup_public,
                        'execution': execution, 'publish_to_start_seconds': execution['start_monotonic'] - publishes[0]['monotonic'],
                        'clear_observed_seconds': time.monotonic() - started}
                    report['phases']['startup_backlog']['oracle'] = equality()
                    # SQL/QuerySet writes bypass model signals; real DB triggers still mark dirty.
                    assert dirty()['count'] == 0
                    before = len(publishes)
                    Listing.objects.filter(pk=bulk.pk).update(status='paused')
                    with connection.cursor() as cursor:
                        cursor.execute('UPDATE listings_listing SET status=%s WHERE id=%s', ['paused', raw.pk])
                        cursor.execute('UPDATE listings_listing SET expires_at=%s WHERE id=%s',
                                       [timezone.now() - timedelta(seconds=1), overdue.pk])
                    assert len(publishes) == before
                    overdue.refresh_from_db()
                    for listing in (bulk, raw, overdue):
                        assert PublicationDirty.objects.filter(listing_id=listing.pk).exists()
                        deny(listing)
                    assert not LifecycleAction.objects.filter(listing=overdue, operation='expire').exists()
                    baseline_version = overdue.lifecycle_version
                    steady_public = public_pages(96, [individual.pk, bulk.pk, raw.pk, overdue.pk])
                    assert all(PublicationDirty.objects.filter(listing_id=row.pk).exists() for row in (bulk, raw, overdue))
                    assert len(publishes) == before
                    phase_b = {'public_pages_before_beat': steady_public,
                               'dirty_before': dirty(), 'zero_harness_signal_publishes': True,
                               'overdue_since_epoch': overdue.expires_at.timestamp()}
                    beat_start = time.monotonic()
                    with (out / 'n07b-beat.log').open('w') as stream:
                        beat = subprocess.Popen([sys.executable, '-m', 'celery', '-A', 'config', 'beat',
                                                 '--loglevel=INFO', '--schedule', str(work / 'beat-schedule')],
                                                env=dict(env, WEB_MODELOS_PROCESS_ROLE='beat'),
                                                stdout=stream, stderr=stream, start_new_session=True)
                    track(beat)

                    def expired_and_refreshed(data):
                        assert beat.poll() is None
                        ticks = [r for r in data if r['event'] == 'publish' and r['role'] == 'beat']
                        if {r['task'] for r in ticks} != {REFRESH, EXPIRE}:
                            return False
                        if PublicationDirty.objects.exists():
                            return False
                        return LifecycleAction.objects.filter(listing=overdue, operation='expire').count() == 1

                    wait(expired_and_refreshed, 150, 'Unchanged publication Beat cadence expired')
                    terminate_owned(beat)
                    data = drain()
                    overdue.refresh_from_db()
                    event = LifecycleAction.objects.get(listing=overdue, operation='expire')
                    assert overdue.status == 'expired' and overdue.lifecycle_version == baseline_version + 1
                    assert event.expected_version == baseline_version and event.actor_id is None
                    assert event.previous_status == 'published' and event.resulting_status == 'expired'
                    assert event.approved_revision_id == overdue.approved_revision_id
                    ticks = [r for r in data if r['event'] == 'publish' and r['role'] == 'beat']
                    assert {r['task'] for r in ticks} == {REFRESH, EXPIRE}
                    assert len([r for r in ticks if r['task'] == EXPIRE]) == 1
                    executions = {r['id']: r for r in data if r['event'] == 'execution'}
                    ledger = []
                    for tick in ticks:
                        execution = executions[tick['id']]
                        delay = execution['start_monotonic'] - tick['monotonic']
                        assert delay >= 0
                        ledger.append({'task': tick['task'], 'id': tick['id'],
                                       'publish_to_start_seconds': delay, 'execution': execution})
                    phase_b.update(beat_started_monotonic=beat_start, beat_publishes=ticks,
                                   task_ledger=ledger,
                                   expiry_event_lag_seconds=(event.created_at - overdue.expires_at).total_seconds(),
                                   expiry_event_count=1, final_dirty=dirty(), oracle=equality())
                    report['phases']['steady_worker_native_beat'] = phase_b
                    # Manual native sweep: this is explicitly not hourly scheduler evidence.
                    with connection.cursor() as cursor:
                        cursor.execute('UPDATE listings_publicationstate SET eligible=NOT eligible WHERE listing_id=%s', [corrupt.pk])
                    assert not PublicationDirty.objects.exists()
                    sweep_id = celery_app.send_task(SWEEP).id
                    data = drain()
                    sweep_execution = next(r for r in data if r['event'] == 'execution' and r['id'] == sweep_id)
                    assert sweep_execution['result'] == 1
                    assert PublicationDirty.objects.filter(listing_id=corrupt.pk).exists()
                    marked = dirty()
                    refresh_id = celery_app.send_task(REFRESH).id
                    drain()
                    report['phases']['manual_sweep'] = {'dispatch': 'Explicit send_task; no hourly cadence claim',
                        'sweep_id': sweep_id, 'refresh_id': refresh_id, 'divergent': 1,
                        'dirty_after_sweep': marked, 'oracle': equality()}
                    assert LifecycleAction.objects.filter(listing=overdue, operation='expire').count() == 1
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
            with connection.cursor() as cursor:
                cursor.execute('SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)', [role])
                report['runtime_role_removed'] = cursor.fetchone()[0]
            report['private_credentials_removed'] = not private_path.exists()
            assert report['runtime_role_removed'] and report['private_credentials_removed']
    finally:
        before_task_publish.disconnect(capture)
        report['harness_publishes'] = publishes
        report['namespace_generation'] = generation
        # Record context-manager cleanup even if a phase raises before success assertions.
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
        if all(identity_gone(pid, ticks) for pid, ticks in identities.items()):
            shutil.rmtree(work)
        report['private_runtime_removed'] = not work.exists()
        (out / 'n07b-publication-runtime.json').write_text(json.dumps(report, allow_nan=False, indent=2) + '\n')
        record_property('n07b_publication_cadence', json.dumps(report, allow_nan=False, sort_keys=True))
    assert report['complete'] and report['foreign_keys_preserved'] and report['unexpected_unscoped_keys'] == 0
    assert 'final_snapshot_error' not in report and 'role_cleanup_snapshot_error' not in report
    assert report['private_runtime_removed'] and report['runtime_role_removed'] and report['private_credentials_removed']
    assert report['worker_exit_code'] == 0 and report['beat_exit_code'] in (0, -15)
    for row in report['events']:
        for field in ('monotonic', 'start_monotonic', 'end_monotonic', 'wall', 'thread_cpu', 'db_wall'):
            if field in row:
                assert isinstance(row[field], (float, int)) and math.isfinite(row[field]) and row[field] >= 0
