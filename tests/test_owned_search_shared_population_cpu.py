"""Current-population CPU experiment; does not enable a product candidate."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Count, Window
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.discovery import candidates
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.benchmark_owned_cpu_observer import owned_pg_pid
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_shared_search_population_cpu(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_search_shared_population_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit owned shared-search CPU diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    owned_pg_pid(run, inspection)
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state')
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
        cursor.execute('SELECT pg_backend_pid()')
        sql_pid = cursor.fetchone()[0]
    identity = owned_backend(run, inspection, sql_pid)
    cases = []
    for term, number in [('photography', 1), ('photography', 2),
                         ('synthetic', 1), ('synthetic', 2), ('zzznomatchproof', 1)]:
        captured = []

        def capture(query, per_page):
            captured.append(query)
            return Paginator(query, per_page)

        with monkeypatch.context() as patch:
            patch.setattr(publication_state, 'Paginator', capture)
            guarded = publication_state.state_page(candidates({'q': term}), number)
        assert guarded is not None and len(captured) == 1
        population = captured[0]
        assert not population.query.distinct
        expected = ([row.pk for row in guarded.object_list], guarded.paginator.count)

        def original():
            page = Paginator(population.all(), 24).page(number)
            return list(page.object_list), page.paginator.count

        def shared():
            offset = (number - 1) * 24
            rows = list(population.all().annotate(_diagnostic_total=Window(Count('*')))
                        .values_list('pk', '_diagnostic_total')[offset:offset + 24])
            assert rows or number == 1  # No claim for empty out-of-range pages.
            return [row[0] for row in rows], rows[0][1] if rows else 0

        blocks = []
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            assert original() == shared() == expected
            for block in range(3):
                order = [('original', original), ('shared', shared)]
                if block % 2:
                    order.reverse()
                for label, operation in order:
                    before = backend_snapshot(identity)
                    for _ in range(8):
                        assert operation() == expected
                    after = backend_snapshot(identity)
                    blocks.append({'block': block, 'variant': label, 'iterations': 8,
                                   'backend_cpu': backend_delta(before, after)})
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            assert cursor.fetchone()[0] == sql_pid
        cases.append({'term': term, 'page': number, 'count': expected[1],
                      'page_size': len(expected[0]), 'blocks': blocks})
    record_property('shared_population_cpu_experiment', cases)
    record_property('backend_host_pid', identity['pid'])
    record_property('scope', 'Five finite current state-population cases, original count+page versus '
                    'COUNT OVER without DISTINCT multipliers; one own readonlyRR snapshot per case. '
                    'Three alternating-order blocks,8iterations per variant per block; exact orderedIDs/count '
                    'checked every operation against existing guarded state_page. No product patch or load. '
                    '100Hz backendCPU quantization; no PostgreSQL statistics extension. No out-of-range, '
                    'dirty/filter race proof, p95, capacity, causal host control or N3. Prior window FAIL retained.')
