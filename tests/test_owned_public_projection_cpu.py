"""Temporary projection CPU experiment, not a maintained product projection."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.discovery import candidates
from apps.listings.models import PublicationDirty
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.benchmark_owned_cpu_observer import owned_pg_pid
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_public_projection_cpu(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_public_projection_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit owned temporary projection diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    owned_pg_pid(run, info)
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state')
    assert not PublicationDirty.objects.exists()
    assert publication_state.all_state_current()
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
        cursor.execute('SELECT pg_backend_pid()')
        sql_pid = cursor.fetchone()[0]
    identity = owned_backend(run, info, sql_pid)
    table = 'cr09_public_projection_diagnostic'
    cases = []
    try:
        # Only this SQL-identified disposable connection. No migration or schema
        # change in the application, no persistent table, no normal service.
        with connection.cursor() as cursor:
            cursor.execute(
                f'CREATE TEMP TABLE {table} AS '
                'SELECT s.listing_id, s.eligible, s.rules_version, '
                'l.expires_at, l.published_at, r.search_document '
                'FROM listings_publicationstate s '
                'JOIN listings_listing l ON l.id=s.listing_id '
                'LEFT JOIN listings_revision r ON r.id=s.revision_id'
            )
            cursor.execute(f'CREATE INDEX ON {table} (published_at DESC, listing_id)')
            cursor.execute(f'ANALYZE {table}')
            cursor.execute('SELECT c.relpersistence, n.nspname FROM pg_class c '
                           'JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=%s::regclass',
                           [table])
            persistence, namespace = cursor.fetchone()
            assert persistence == 't' and namespace.startswith('pg_temp_')
        for term, number in [('', 1), ('', 2), ('photography', 1), ('photography', 2),
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
            _, params = population.query.sql_with_params()
            cutoffs = [p for p in params if isinstance(p, datetime)]
            assert len(cutoffs) == 1
            expected = ([row.pk for row in guarded.object_list], guarded.paginator.count)
            where = 'eligible AND rules_version=%s AND expires_at>%s'
            values = [publication_state.rules_version(), cutoffs[0]]
            search = "(websearch_to_tsquery('spanish'::regconfig,%s) || " \
                     "websearch_to_tsquery('english'::regconfig,%s))"
            ordering, rank_values = 'published_at DESC, listing_id', []
            if term:
                where += ' AND search_document @@ ' + search
                values += [term, term]
                ordering = 'ts_rank(search_document,' + search + ') DESC, ' + ordering
                rank_values = [term, term]

            def original():
                page = Paginator(population.all(), 24).page(number)
                return list(page.object_list), page.paginator.count

            def projected():
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE ' + where, values)
                    count = cursor.fetchone()[0]
                    cursor.execute(f'SELECT listing_id FROM {table} WHERE ' + where
                                   + ' ORDER BY ' + ordering + ' LIMIT 24 OFFSET %s',
                                   values + rank_values + [(number - 1) * 24])
                    ids = [row[0] for row in cursor.fetchall()]
                return ids, count

            blocks = []
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                assert original() == projected() == expected
                variants = [('original', original), ('projected', projected)]
                for _, operation in variants:
                    for _ in range(4):
                        assert operation() == expected
                for block in range(3):
                    for label, operation in variants if block % 2 == 0 else list(reversed(variants)):
                        before = backend_snapshot(identity)
                        for _ in range(8):
                            assert operation() == expected
                        after = backend_snapshot(identity)
                        blocks.append({'block': block, 'variant': label, 'iterations': 8,
                                       'backend_cpu': backend_delta(before, after)})
            cases.append({'term': term, 'page': number, 'count': expected[1], 'blocks': blocks})
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS pg_temp.{table}')
    record_property('public_projection_cpu', {'cases': cases, 'backend_host_pid': identity['pid'],
                    'temporary_table_removed': True})
    record_property('scope', 'Static synthetic10k parent/state/revision data copied once into own '
                    'session temporary table; paired exact count+orderedIDs vs current guarded '
                    'population for7finite cases. Same readonlyRR percase;4warmups+3alternating '
                    'blocks8operations each, CPU100Hz. No mutations between copy/read. '
                    'No maintenance/freshness/race/filter-general proof, model/migration, product '
                    'replacement, p95, capacity or N3. A static projection alone is unsafe for live data.')
