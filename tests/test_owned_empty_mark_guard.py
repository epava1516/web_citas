"""Owned-only empty-mark control; no migration or production function replacement."""
import importlib
import json
import os
import subprocess
import statistics
import time
import uuid
from pathlib import Path

import pytest
from django.db import DatabaseError, connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("protocol", ["as_recorded", "quiescent_cold"])
def test_owned_empty_mark_guard(request, record_property, protocol):
    if not any(str(x).split('::')[0] == 'tests/test_owned_empty_mark_guard.py'
               for x in request.config.args):
        pytest.skip('Explicit owned empty-mark diagnostic only')
    request.getfixturevalue('directory')
    data = populate(10000)
    publication_state.refresh_all()
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    pg_group = None
    if protocol == 'quiescent_cold':
        from scripts.benchmark_owned_cpu_observer import cpu_delta, group_path, owned_pg_pid, read_group

        out = Path(request.config.getoption('--gate-timings-output')).parent
        run = json.loads((out/'runner.json').read_text())
        name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
        inspection = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
        pg_group = group_path(owned_pg_pid(run, inspection))
        assert inspection['Id'] in str(pg_group)
    source = importlib.import_module('apps.listings.migrations.0020_publication_match_counterparts').MARK
    functions = {'original': 'owned_cr09_mark_original', 'guard': 'owned_cr09_mark_guard'}
    with connection.cursor() as cursor:
        cursor.execute("SELECT prosrc FROM pg_proc WHERE oid='listings_publication_mark(uuid[])'::regprocedure")
        original_body = cursor.fetchone()[0]
        assert original_body == source.split('$$')[1]
        for arm, name in functions.items():
            sql = source.replace('FUNCTION listings_publication_mark(', 'FUNCTION '+name+'(')
            if arm == 'guard':
                assert sql.count('BEGIN\n') == 1
                sql = sql.replace('BEGIN\n', 'BEGIN\n  IF ids IS NULL OR cardinality(ids)=0 THEN RETURN; END IF;\n')
            cursor.execute(sql)
    controls, samples = [], []
    version = publication_state.rules_version()
    try:
        for case, ids in [('null', None), ('empty', []), ('null_element', [None]),
                          ('valid', [data['sample_ids'][0]]),
                          ('duplicate_null', [data['sample_ids'][0], None, data['sample_ids'][0]]),
                          ('absent_listing', [str(uuid.uuid4())]),
                          ('malformed_uuid', ['synthetic-invalid-uuid']),
                          ('valid_twice', [data['sample_ids'][0]])]:
            outcomes = []
            for arm, name in functions.items():
                PublicationDirty.objects.all().delete()
                with connection.cursor() as cursor:
                    cursor.execute('SELECT last_value FROM listings_publication_generation')
                    before = cursor.fetchone()[0]
                error = None
                try:
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT '+name+'(%s::uuid[])', [ids])
                        if case == 'valid_twice':
                            timestamps = dict(PublicationDirty.objects.values_list('listing_id', 'marked_at'))
                            with connection.cursor() as cursor:
                                cursor.execute('SELECT '+name+'(%s::uuid[])', [ids])
                            assert dict(PublicationDirty.objects.values_list('listing_id', 'marked_at')) == timestamps
                except DatabaseError as exc:
                    error = exc.__cause__.sqlstate
                rows = sorted(str(x) for x in PublicationDirty.objects.values_list('listing_id', flat=True))
                with connection.cursor() as cursor:
                    cursor.execute('SELECT last_value FROM listings_publication_generation')
                    delta = cursor.fetchone()[0]-before
                outcomes.append(dict(rows=rows, generation_delta=delta, error=error))
            assert outcomes[0] == outcomes[1]
            if case in ('null', 'empty', 'null_element'):
                assert outcomes[0] == dict(rows=[], generation_delta=0, error=None)
            if case == 'absent_listing':
                assert outcomes[0] == dict(rows=ids, generation_delta=1, error=None)
            if case == 'malformed_uuid':
                assert outcomes[0] == dict(rows=[], generation_delta=0, error='22P02')
            controls.append(dict(case=case, outcome=outcomes[0]))
        PublicationDirty.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM listings_listing l LEFT JOIN listings_publicationstate s '
                           'ON s.listing_id=l.id WHERE s.listing_id IS NULL OR s.rules_version<>%s', [version])
            assert cursor.fetchone()[0] == 0
        for scope in ['direct_empty', 'complete_mark_stale']:
            for block, order in enumerate(['ABC', 'BCA', 'CAB']):
                for arm in order:
                    arm_started = time.perf_counter()
                    connection.close()
                    connection.ensure_connection()
                    name = functions['guard' if arm == 'C' else 'original']
                    sql = ('SELECT '+name+'(ARRAY[]::uuid[])' if scope == 'direct_empty' else
                           'SELECT '+name+'(ARRAY(SELECT l.id FROM listings_listing l LEFT JOIN '
                           'listings_publicationstate s ON s.listing_id=l.id WHERE s.listing_id IS NULL '
                           'OR s.rules_version<>%s))')
                    params = None if scope == 'direct_empty' else [version]
                    with connection.cursor() as cursor:
                        cursor.execute("SET statement_timeout='5s'")
                        cursor.execute('SELECT pg_backend_pid()')
                        pid = cursor.fetchone()[0]
                        if pg_group:
                            time.sleep(.150)  # Fixed diagnostic separation; identical in every arm.
                            group_before = read_group(pg_group)
                        wall, cpu = time.perf_counter(), time.thread_time()
                        cursor.execute(sql, params)
                        cursor.fetchone()
                        first_wall, first_cpu = time.perf_counter()-wall, time.thread_time()-cpu
                        group_cost = cpu_delta(group_before, read_group(pg_group)) if pg_group else None
                        warm = []
                        for _ in range(12):
                            begin = time.perf_counter()
                            cursor.execute(sql, params)
                            cursor.fetchone()
                            warm.append(time.perf_counter()-begin)
                    samples.append(dict(scope=scope, block=block, arm=arm, backend_pid=pid,
                                        first_wall=first_wall, first_app_cpu=first_cpu,
                                        warm_wall=warm, pg_group_cost=group_cost,
                                        arm_total_seconds=time.perf_counter()-arm_started))
        assert len({x['backend_pid'] for x in samples}) == 18
        comparisons = []
        for scope in ['direct_empty', 'complete_mark_stale']:
            means = {arm:statistics.mean(x['first_wall'] for x in samples
                                       if x['scope']==scope and x['arm']==arm) for arm in 'ABC'}
            reference = statistics.mean([means['A'], means['B']])
            nonregression = [
                next(x['first_wall'] for x in samples if x['scope']==scope and x['block']==block
                     and x['arm']=='C') <= statistics.mean(x['first_wall'] for x in samples
                     if x['scope']==scope and x['block']==block and x['arm'] in 'AB')
                for block in range(3)
            ]
            comparisons.append(dict(scope=scope, means=means,
                                    nonregression_blocks=nonregression,
                                    aa_relative_difference=abs(means['A']-means['B'])/reference,
                                    candidate_to_reference=means['C']/reference))
        with connection.cursor() as cursor:
            cursor.execute("SELECT prosrc FROM pg_proc WHERE oid='listings_publication_mark(uuid[])'::regprocedure")
            assert cursor.fetchone()[0] == original_body
        result = dict(protocol=protocol, controls=controls, samples=samples, comparisons=comparisons,
                      diagnostic_separation_seconds=.150 if pg_group else 0,
                      limits='Own synthetic10k, temporary clone functions, native function unchanged. '
                             '18 fresh physical backends, first operation includes exterior scan in '
                             'complete scope;12 warm repeats separate. No concurrency/worker/HTTP or '
                             'PostgreSQL per-query CPU claim; client CPU is not backend CPU. Quiescent '
                             'protocol adds fixed150ms outside first-call clock, included in arm total; '
                             'own PG cgroup counters include background and collector fencing. '
                             'Not an operational policy or exclusion of HTTP arrivals. No automatic adoption.')
        out = Path(request.config.getoption('--gate-timings-output')).parent
        (out/('empty-mark-guard-'+protocol+'.json')).write_text(json.dumps(result, indent=2)+'\n')
        record_property('empty_mark_guard', json.dumps(comparisons))
    finally:
        for name in functions.values():
            with connection.cursor() as cursor:
                cursor.execute('DROP FUNCTION '+name+'(uuid[])')
