"""Finite consumer diagnosis; real PG/TCP, separate count and original A/A corpus."""
import http.cookiejar
import json
import time
import urllib.request
from urllib.parse import urlencode
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from capacity_target_fixture import PATHS, populate
from django.db import connection, transaction
from test_capacity_chain_inline_http import clone_server, owned_server
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




def test_scalar_consumers_committed_http_clones(request, settings, monkeypatch, tmp_path, record_property):
    assert connection.vendor == 'postgresql' and validated_kernel() is not None
    request.getfixturevalue('directory')
    identity = 'scalar-consumers-synthetic'
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
    from apps.safety.evidence_chain_sql_v1 import EVENT
    # Seed real audited history once, before closing every connection for TEMPLATE.
    with owned_server(settings, tmp_path) as (endpoint, _):
        url = endpoint + f'/en/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/'
        with client.open(url, timeout=60) as response:
            response.read()
        csrf = next(cookie.value for cookie in cookiejar if cookie.name == settings.CSRF_COOKIE_NAME)
        def request_body():
            return urlencode({'operation': 'inspect', 'key': str(uuid4()), 'version': case.version,
                              'reason': REASON, 'dataset': 'revisions', 'row_number': 1,
                              'field_page': 1, 'page_count': 4}).encode()
        for _ in range(64):
            query = urllib.request.Request(url, data=request_body(), headers={
                'Content-Type': 'application/x-www-form-urlencoded', 'Referer': url, 'X-CSRFToken': csrf})
            with client.open(query, timeout=120) as response:
                assert response.status == 200
                response.read()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT count(*) FROM public."{EVENT}" WHERE request_id=%s', [case.pk])
        initial_events = cursor.fetchone()[0]
    initial_reads = RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count()
    measurements = []
    warmed_pids = set()
    with clone_server(settings, tmp_path, "tests.capacity_scalar_wsgi:application") as (endpoint, output, clone, release, database):
        url = endpoint + f'/en/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/'
        def post(mode, target):
            if output.exists():
                output.unlink()
            query = urllib.request.Request(url, data=request_body(), headers={
                'Content-Type': 'application/x-www-form-urlencoded', 'Referer': url, 'X-CSRFToken': csrf,
                'X-Chain-Clone': target, 'X-Chain-Variant': mode})
            wall = time.perf_counter_ns()
            with client.open(query, timeout=120) as response:
                assert response.status == 200 and 'no-store' in response.headers['Cache-Control']
                size = len(response.read())
                pid = int(response.headers['X-Benchmark-Pid'])
            tcp = time.perf_counter_ns() - wall
            deadline = time.monotonic() + 10
            while not output.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            assert output.exists()
            value = json.loads(output.read_text())
            assert value['pid'] == pid and value['mode'] == mode
            value.update(tcp_ns=tcp, response_bytes=size)
            # Independent owner inspection after normal service commits, never a rollback wrapper.
            import psycopg
            with psycopg.connect(dbname=target, user=database['USER'], password=database['PASSWORD'],
                                 host=database['HOST'], port=database['PORT']) as inspect:
                with inspect.cursor() as cursor:
                    cursor.execute(f'SELECT count(*) FROM public."{EVENT}" WHERE request_id=%s', [case.pk])
                    assert cursor.fetchone() == (initial_events + 8,)
                    cursor.execute('SELECT count(*) FROM safety_rightsportabilitycoverageread WHERE coverage_id=%s',
                                   [coverage.pk])
                    assert cursor.fetchone() == (initial_reads + 4,)
            release(target)
            return value
        # Real POST warmups for both workers; each uses its own identical clone.
        for number in range(12):
            value = post('control', clone())
            warmed_pids.add(value['pid'])
            if number >= 3 and len(warmed_pids) == 2:
                break
        assert len(warmed_pids) == 2
        for mode in ('control', 'spans', 'control'):
            value = post(mode, clone())
            value.update(events_before=initial_events, events_after=initial_events+8)
            measurements.append(value)
            record_property('scalar_consumer_sample', json.dumps(value))
        observed = measurements[1]['diagnostic']['spans']
        assert observed['source_copy']['calls'] == 1
        assert observed['compile_coverage']['calls'] == 1
        assert observed['project_selected']['calls'] == 2
        assert observed['coverage_page']['calls'] == 4
        census = post('count', clone())  # separate clone, entirely excluded from timing comparisons
        record_property('scalar_consumer_count', json.dumps(census))
        counted = census['diagnostic']
        assert counted['calls']['compile_coverage'] == 1
        assert counted['calls']['project_selected'] == 2
        assert counted['calls']['coverage_page'] == 4
        from tests.capacity_scalar_diagnostic import benchmark, source_census
        expected_census = source_census(source)
        assert counted['source'] == expected_census
        compile_sites = [item for site, item in counted['sites'].items()
                         if site.startswith('apps.safety.rights_portability_coverage:')]
        assert sum(item['calls'] for item in compile_sites) == sum(
            item['rows'] for item in counted['compile_rows'].values())
        assert sum(item['leaves_yielded'] for item in compile_sites) == sum(
            item['leaves'] for item in counted['compile_rows'].values())
    # No server or active HTTP measurement while the original A/A microbench runs.
    rows = [row for reader in SECTIONS.values() for row in reader(source)]
    pointer_inputs = []
    for dataset, selectors in body['selection'].items():
        references = {row_reference(dataset, index, row): row
                      for index, row in enumerate(SECTIONS[dataset](source))}
        pointer_inputs.extend((references[selector['row']], path)
                              for selector in selectors for path in selector['fields'])
    pure = benchmark(rows, pointer_inputs)
    assert source_census(source) == expected_census
    record_property('scalar_original_AA', json.dumps(pure))
    report = dict(samples=measurements, initial_events=initial_events, initial_reads=initial_reads,
                  warmed_workers=len(warmed_pids), selected_bytes=selected_bytes, samples_per_variant=None,
                  census=census, pure_original_AA=pure, same_measured_pid=len({s["pid"] for s in measurements}) == 1,
                  scope='finite_scalar_consumers_control_spans_control_count_and_original_AA_not_capacity',
                  limits=['New connection per sample; database clones share schema/statistics/history, not buffer identity',
                          'Partial scalar coverage; no Caddy/RustFS/quotas/concurrent load',
                          'Fresh clone connection cost included; only eight consumer timers, no SQL observer or CPU profiler; no outer transaction',
                          'Real warm POSTs on both workers, SQL caches per database/connection may differ'])
    record_property('scalar_consumer_report', json.dumps(report))
