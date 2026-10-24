"""Measure planner metadata after full synthetic preparation; not product ROI."""

import hashlib
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

import pytest
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.core.models import Person, RepresentationAction, User, VerificationCheck
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision
from apps.mediafiles.models import Photo
from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend, statement_family

pytestmark = pytest.mark.django_db(transaction=True)
TARGETS = [User, Person, RepresentationAction, VerificationCheck, PromotionOrder,
           PromotionEntitlement, PublicationState, Revision.categories.through]
TABLES = TARGETS + [Listing, Revision, Photo]


def data_checksums():
    result = {}
    for model in TABLES:
        table = connection.ops.quote_name(model._meta.db_table)
        pk = connection.ops.quote_name(model._meta.pk.column)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT count(*), encode(sha256(convert_to(COALESCE("
                           f"string_agg(to_jsonb(t)::text, chr(10) ORDER BY t.{pk}), ''), 'UTF8')), 'hex') "
                           f"FROM {table} t")
            count, digest = cursor.fetchone()
        result[model._meta.db_table] = {'rows': count, 'sha256': digest}
    return result


def planner_metadata():
    tables = [model._meta.db_table for model in TABLES]
    with connection.cursor() as cursor:
        cursor.execute('''SELECT c.relname, c.reltuples, s.n_live_tup, s.n_mod_since_analyze,
                                 s.last_analyze, s.last_autoanalyze, s.analyze_count, s.autoanalyze_count
                          FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                          LEFT JOIN pg_stat_all_tables s ON s.relid=c.oid
                          WHERE n.nspname=current_schema() AND c.relname=ANY(%s)
                          ORDER BY c.relname''', [tables])
        columns = [c.name for c in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def prepared_metadata():
    with connection.cursor() as cursor:
        cursor.execute('SELECT name, statement, generic_plans, custom_plans FROM pg_prepared_statements ORDER BY name')
        return [{'name': name, 'statement_sha256': hashlib.sha256(statement.encode()).hexdigest(),
                 'family': statement_family(statement), 'generic_plans': generic, 'custom_plans': custom}
                for name, statement, generic, custom in cursor.fetchall()]


def test_statistics_after_promotional_fixture(request, settings, record_property):
    run_id = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert not publication_state.READ_REPAIR and not connection.in_atomic_block
    settings.PROMOTION_TEST_MODE = True
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run_id
    runner = json.loads((folder / 'runner.json').read_text())
    container = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert container == 'web-modelos-ci-pg-' + run_id
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]
    prepare_promotional_load(request, 1000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    client = request.getfixturevalue('directory')
    original_data = data_checksums()
    before_metadata = planner_metadata()
    stages, signatures = [], {}
    reads = 0

    def read(path):
        nonlocal reads
        reads += 1
        response = client.get(path)
        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
        assert response.wsgi_request._publication_route['route'] == 'state'
        page = response.context['page']
        assert page.paginator.count == 1000 and len(page.object_list) == 24
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list),
                tuple(c['sponsorship'] for c in response.context['cards']))

    def snapshot(identity):
        row = backend_snapshot(identity)
        sched = list(map(int, Path(f"/proc/{identity['pid']}/schedstat").read_text().split()))
        return row | {'runtime_ns': sched[0]}

    for stage in ['native_preparation', 'explicit_post_preparation_analyze']:
        analyze_seconds = None
        if stage == 'explicit_post_preparation_analyze':
            start = time.perf_counter()
            for model in TARGETS:
                with connection.cursor() as cursor:
                    cursor.execute('ANALYZE ' + connection.ops.quote_name(model._meta.db_table))
            analyze_seconds = time.perf_counter() - start
        entry = {'stage': stage, 'metadata_before': planner_metadata(), 'routes': [],
                 'analyze_seconds': analyze_seconds}
        for route, path in [('directory_es', '/es/'), ('search_en', '/en/?q=synthetic')]:
            connection.close()  # Same fresh-backend policy on both sides, outside clocks.
            signature = read(path)
            signatures.setdefault(route, signature)
            assert signature == signatures[route]
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                sql_pid = cursor.fetchone()[0]
            identity = owned_backend(runner, inspection, sql_pid)
            initial_prepared = prepared_metadata()
            samples = []
            for _ in range(6):
                before = snapshot(identity)
                wall, cpu = time.perf_counter(), time.thread_time()
                actual = read(path)
                wall, cpu = time.perf_counter() - wall, time.thread_time() - cpu
                after = snapshot(identity)
                assert actual == signature and after['runtime_ns'] >= before['runtime_ns']
                samples.append({'wall': wall, 'app_cpu': cpu,
                                'backend_cpu': (after['runtime_ns'] - before['runtime_ns']) / 1e9,
                                'backend_before': before, 'backend_after': after,
                                'prepared_after_outside_clock': prepared_metadata()})
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                assert cursor.fetchone()[0] == sql_pid
            entry['routes'].append({'route': route, 'backend_identity': identity, 'samples': samples,
                                    'prepared_after_warm': initial_prepared,
                                    'median_wall': statistics.median(x['wall'] for x in samples)})
        entry['metadata_after'] = planner_metadata()
        assert data_checksums() == original_data
        stages.append(entry)
    after_metadata = planner_metadata()
    target_names = {model._meta.db_table for model in TARGETS}
    for row in after_metadata:
        if row['relname'] in target_names:
            assert abs(row['reltuples'] - original_data[row['relname']]['rows']) <= max(
                1, original_data[row['relname']]['rows'] * 0.02,
            )
    assert reads == 28 and not PublicationDirty.objects.exists()
    stale_before = [row['relname'] for row in before_metadata if row['relname'] in target_names
                    and abs(row['reltuples'] - original_data[row['relname']]['rows']) > max(
                        1, original_data[row['relname']]['rows'] * 0.02)]
    data = {'run_id': run_id, 'result': 'POST_FIXTURE_STATISTICS_DIAGNOSIS_NOT_ROI',
            'profiles': 1000, 'rights': 200, 'http_reads': reads, 'stages': stages,
            'tables_analyzed': sorted(target_names), 'stale_estimates_before': stale_before,
            'metadata_before': before_metadata, 'metadata_after': after_metadata,
            'domain_checksums_unchanged': original_data, 'product_changed': False,
            'limits': ['Fixed native-then-analyze order; warm cache/time/autovacuum not causally isolated',
                       'No GUC, resource, index, constraint, driver policy or domain-row change',
                       'Prepared and table metadata outside clocks; no SQL text or parameters stored',
                       'Small1000/200 diagnostic; no10000/2000 TCP or product speedup verdict',
                       'Original TCP FAIL and rejected candidates preserved; no automatic fixture adoption']}
    output = folder / 'beta-post-fixture-statistics.json'
    output.write_text(json.dumps(data, indent=2, default=str) + '\n')
    record_property('post_fixture_statistics_reads', reads)
    record_property('post_fixture_statistics_sha256', hashlib.sha256(output.read_bytes()).hexdigest())
