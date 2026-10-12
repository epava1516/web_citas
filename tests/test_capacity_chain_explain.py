"""Finite actual SQL plans at two service-generated history sizes, runtime LOGIN."""
import http.cookiejar
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from capacity_runtime_role import runtime_role_environment
from capacity_target_fixture import PATHS, populate
from django.db import connection, transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_review_http import login

from apps.core.models import User
from apps.safety.canonical_kernel_loader import validated_kernel
from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityCoverageRead
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, reviewer_case, source_copy
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_selection import project_selected, row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)
REASON = 'Diagnose one independently audited synthetic large coverage batch'


@contextmanager
def owned_server(settings, tmp_path):
    # No baseline fallback and no Celery/export/finish path.
    name = 'unseal_batch_settings_' + uuid4().hex
    (tmp_path / (name + '.py')).write_text(
        f"from {os.environ['DJANGO_SETTINGS_MODULE']} import *\n"
        + f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        + "RIGHTS_VERIFICATION_BACKEND = 'simulator'\n"
        + 'CELERY_TASK_ALWAYS_EAGER = True\n')
    output = tmp_path / 'one-batch.json'
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    with runtime_role_environment(name) as overrides:
        env = os.environ.copy()
        env.update(overrides)
        env['PYTHONPATH'] = str(tmp_path) + os.pathsep + env['PYTHONPATH']
        env['CHAIN_DIAGNOSTIC_OUTPUT'] = str(output)
        with (tmp_path / 'gunicorn.log').open('w') as log:
            process = subprocess.Popen(
                [sys.executable, '-m', 'gunicorn', 'tests.capacity_chain_wsgi:application',
                 '--workers', '2', '--worker-class', 'sync', '--bind', f'127.0.0.1:{port}',
                 '--timeout', '120', '--logger-class', 'config.gunicorn_logging.SafeAccessLogger'],
                env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                endpoint = f'http://127.0.0.1:{port}'
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError('Owned Gunicorn failed before readiness')
                    try:
                        with urllib.request.urlopen(endpoint + '/health/', timeout=2) as response:
                            assert response.status == 200
                            break
                    except OSError:
                        if time.monotonic() > deadline:
                            raise RuntimeError('Owned Gunicorn readiness timeout') from None
                        time.sleep(0.1)
                yield endpoint, output
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=10)


def test_chain_plans_with_real_history(request, settings, monkeypatch, tmp_path, record_property):
    assert connection.vendor == 'postgresql' and validated_kernel() is not None
    request.getfixturevalue('directory')
    identity = 'chain-explain-synthetic'
    _, _, _, manifest = populate(identity)
    original_ready = fixtures.ready

    def ready(*args, **kwargs):
        return original_ready(*args, **(kwargs | {'subject_username': identity}))

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, 'ready', ready)
        case, author, baseline, previous, person, _, _ = fixtures.prepared_selection(
            request, settings, patch, False)
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    assert len(source['revisions']) == 1500
    body = unseal(baseline.encrypted_selection)
    body['selection']['revisions'] = [
        {'row': row_reference('revisions', index, row), 'fields': PATHS}
        for index, row in enumerate(source['revisions'])]
    selection = save_selection(author, case.pk, case.version, baseline.assessment_review_id,
                               uuid4(), baseline.version, REASON, body['selection'],
                               field_evidence=body['field_evidence'])
    projected = project_selected(source, unseal(selection.assessment_review.assessment.encrypted_assessment),
                                 body['selection'], field_evidence=body['field_evidence'])
    selected_bytes = len(canonical(projected).encode())
    assert abs(selected_bytes - 16 * 1024 * 1024) / (16 * 1024 * 1024) < .01
    reviewer = User.objects.get(pk=previous.action.actor_id)
    # Genuine paged reads, no fabricated IDs/approvals; inspect every selected row.
    for page in range(1, 32):
        record(reviewer, case.pk, case.version, selection.pk, uuid4(), REASON, page=page)
    decision, _ = record(reviewer, case.pk, case.version, selection.pk, uuid4(), REASON,
                         'review', 'approved', _require_pages=True)
    assert len(decision.page_reads) == 31
    coverage = save_coverage(author, case.pk, case.version, decision.pk, uuid4(), 0,
                             REASON, {name: {} for name in SECTIONS}, {}, allow_partial=True)
    browser = login(reviewer, csrf=True)
    cookiejar = http.cookiejar.CookieJar()
    cookiejar.set_cookie(http.cookiejar.Cookie(
        0, settings.SESSION_COOKIE_NAME, browser.cookies[settings.SESSION_COOKIE_NAME].value,
        None, False, '127.0.0.1', False, False, '/', True, False, None, True, None, None, {}))
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    with owned_server(settings, tmp_path) as (endpoint, output):
        url = endpoint + f'/en/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/'
        with client.open(url, timeout=60) as response:
            assert response.status == 200
            response.read()  # Initial open excluded; load domain aliases before observation.
        csrf = next(cookie.value for cookie in cookiejar if cookie.name == settings.CSRF_COOKIE_NAME)
        from apps.safety.evidence_chain_sql_v1 import EVENT

        def events():
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT count(*) FROM public."{EVENT}" WHERE request_id=%s', [case.pk])
                return cursor.fetchone()[0]

        levels = []
        seeded = 0
        started_experiment = time.monotonic()

        def post():
            before = events()
            before_reads = RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count()
            data = urlencode({'operation': 'inspect', 'key': str(uuid4()), 'version': case.version,
                              'reason': REASON, 'dataset': 'revisions', 'row_number': 1,
                              'field_page': 1, 'page_count': 4}).encode()
            query = urllib.request.Request(url, data=data, headers={
                'Content-Type': 'application/x-www-form-urlencoded', 'Referer': url, 'X-CSRFToken': csrf})
            with client.open(query, timeout=120) as response:
                assert response.status == 200 and 'no-store' in response.headers['Cache-Control']
                response.read()
            assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == before_reads + 4
            assert events() == before + 8

        final_target = getattr(settings, 'CAPACITY_SQL_PLAN_TARGET', None) or 64
        assert final_target in (64, 304)
        record_property('chain_plan_target', str(final_target))
        for target in (0, final_target):
            while seeded < target:
                assert time.monotonic() - started_experiment < 420, 'Finite preparation budget exhausted'
                post()
                seeded += 1
                if seeded % 8 == 0:
                    Path('/tmp/capacity-chain-plan-progress.json').write_text(json.dumps({
                        'seeded_batches': seeded, 'target': final_target,
                        'head_count': events(),
                        'elapsed_seconds': time.monotonic() - started_experiment,
                        'preparation_budget_seconds': 420,
                    }))
            before = events()
            # Independent restricted LOGIN, not SET ROLE on an owner connection.
            # Close this child before role/credential cleanup and next HTTP write.
            destination = tmp_path / f'plans-{target}.json'
            with runtime_role_environment(os.environ['DJANGO_SETTINGS_MODULE']) as overrides:
                env = os.environ.copy()
                env.update(overrides)
                result = subprocess.run(
                    [sys.executable, '-m', 'tests.capacity_chain_explain', str(case.pk), str(destination)],
                    env=env, capture_output=True, text=True, timeout=90)
                assert result.returncode == 0, 'Own explain child failed: ' + result.stderr[-3000:]
            assert events() == before
            level = json.loads(destination.read_text())
            level['seeded_batches'] = seeded
            assert level['head_count'] == before and level['runtime_login_verified']
            assert len(level['queries']) == 8
            assert all(query['inline_exact'] for query in level['queries'])
            levels.append(level)
            record_property('chain_explain_level', json.dumps(level))
    report = dict(levels=levels, seeded_batches=seeded, selected_bytes=selected_bytes,
                  originals_bytes=manifest['originals_bytes'],
                  experiment_wall_seconds=time.monotonic() - started_experiment,
                  limits=['New synthetic case, two sequential sizes, warm diagnostic plans only',
                          'Service-approved partial scalar coverage, no binary deliveries or exports',
                          'Runtime LOGIN; HTTP seed Gunicorn2 local; no Caddy/RustFS/contractual quotas',
                          'TIMING OFF four rotated rounds; one timed native and one SERIALIZE TEXT native',
                          'Projection/width changes may alter plans; shape equality explicitly reported',
                          'Whole-row/jsonb/inline are test controls, never production validation shortcuts',
                          'No manual ANALYZE, indexes or planner switches; statistics inventory retained',
                          'EXPLAIN does not send result rows or measure Python result adaptation/network'])
    record_property('chain_explain_report', json.dumps(report))
