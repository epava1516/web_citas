"""Exact coverage aggregate comparison, no product SQL replacement."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.models import Listing, PublicationState
from apps.listings.publication_state import all_state_current, rules_version
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.benchmark_owned_cpu_observer import owned_pg_pid
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

ORIGINAL = (
    'SELECT NOT EXISTS (SELECT 1 FROM listings_publicationstate WHERE rules_version <> %s) '
    'AND (SELECT COUNT(*) FROM listings_publicationstate) = (SELECT COUNT(*) FROM listings_listing)'
)
ONE_PASS = (
    'SELECT COUNT(*) = (SELECT COUNT(*) FROM listings_listing) '
    'AND COALESCE(bool_and(rules_version = %s), true) FROM listings_publicationstate'
)


def test_owned_state_coverage_aggregate_cpu(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_state_aggregate_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit owned coverage aggregate diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    owned_pg_pid(run, inspection)

    def operation(sql):
        with connection.cursor() as cursor:
            cursor.execute(sql, [rules_version()])
            return cursor.fetchone()[0]

    assert not Listing.objects.exists() and not PublicationState.objects.exists()
    assert operation(ORIGINAL) is operation(ONE_PASS) is True
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state')
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
        cursor.execute('SELECT pg_backend_pid()')
        sql_pid = cursor.fetchone()[0]
    identity = owned_backend(run, inspection, sql_pid)
    target = PublicationState.objects.first()
    cases = []
    for kind, expected in [('current', True), ('ineligible', True), ('stale', False), ('missing', False)]:
        if kind == 'ineligible':
            PublicationState.objects.filter(pk=target.pk).update(eligible=False)
        elif kind == 'stale':
            PublicationState.objects.filter(pk=target.pk).update(rules_version='obsolete-rule')
        elif kind == 'missing':
            PublicationState.objects.filter(pk=target.pk).delete()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            assert all_state_current() is expected
            assert all_state_current(trusted_snapshot=True) is expected
            variants = [('original', ORIGINAL), ('one_pass', ONE_PASS)]
            for _, sql in variants:
                for _ in range(8):
                    assert operation(sql) is expected
            blocks, plans = [], []
            for block in range(3):
                for label, sql in variants if block % 2 == 0 else list(reversed(variants)):
                    before = backend_snapshot(identity)
                    for _ in range(12):
                        assert operation(sql) is expected
                    after = backend_snapshot(identity)
                    blocks.append({'block': block, 'variant': label, 'iterations': 12,
                                   'backend_cpu': backend_delta(before, after)})
            for label, sql in variants:
                with connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, [rules_version()])
                    plan = cursor.fetchone()[0][0]
                scans = []

                def walk(node):
                    if 'Relation Name' in node:
                        scans.append({k: node[k] for k in ('Node Type', 'Relation Name',
                                                          'Actual Rows', 'Actual Loops') if k in node})
                    for child in node.get('Plans', []):
                        walk(child)

                walk(plan['Plan'])
                plans.append({'variant': label, 'planning_ms': plan['Planning Time'],
                              'execution_ms': plan['Execution Time'], 'scans': scans})
            cases.append({'kind': kind, 'expected': expected, 'blocks': blocks, 'plans': plans})
    record_property('state_aggregate_cpu', {'cases': cases, 'backend_host_pid': identity['pid'],
                    'empty_population_correct': True})
    record_property('scope', 'Owned 10k synthetic committed FK-consistent population; current/ineligible/'
                    'stale/missing states and separate empty control, original vs combined aggregate. '
                    'Same own readonlyRR snapshot per case,8warmups+3alternating blocks12iterations, '
                    'raw booleans checked every operation against original join; CPU100Hz. '
                    'No product replacement, inherited transaction guarantee, load, p95 or N3.')
