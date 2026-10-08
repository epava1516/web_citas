"""Owned PostgreSQL prototype: distinguish query shape from partial-index effect."""
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models.expressions import Col
from django.db.models.sql.query import Query
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Rate, Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('TEXT_INDEX_PROBE_OUTPUT'), reason='Explicit owned PostgreSQL prototype only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_text_unknown_partial_index_mechanism(request, monkeypatch, record_property, variant):
    request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        revisions = list(Revision.objects.filter(status='approved').order_by('pk'))
        for i, row in enumerate(revisions):
            suffix = alpha(i)
            row.description += ' '+suffix
            if row.description_alternative:
                row.description_alternative += ' '+suffix
            row.telegram = 'bench'+suffix
        Revision.objects.bulk_update(revisions, ['description', 'description_alternative', 'telegram'], batch_size=250)
    assert connection.vendor == 'postgresql' and projection.supported()
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    fingerprint = projection.definitions_digest()
    specs = {Revision: [('title', 120, True), ('description', 6000, True), ('description_alternative', 6000, False)],
             Rate: [('concept', 80, True)]}
    predicates, indexes = {}, {}
    for model, fields in specs.items():
        query = Query(model, alias_cols=False)
        condition = Q()
        for field, maximum, required in fields:
            condition &= Q(proof.PlainTextProof(F(field), maximum, required, legacy=True))
        where = query.build_where(condition)
        sql, params = where.as_sql(query.get_compiler(connection=connection), connection)
        predicates[model] = ('('+sql+') IS NOT TRUE', params)
        indexes[model] = 'probe_text_unknown_' + model._meta.model_name

    compiled = {}
    original_text = proof.PlainTextProof.as_sql

    def membership(self, compiler, database, **kwargs):
        column = self.source_expressions[0]
        assert isinstance(column, Col)
        model, name = column.target.model, column.target.name
        if model is Revision and name in {'description', 'description_alternative'}:
            return 'TRUE', []
        assert (model is Revision and name == 'title') or (model is Rate and name == 'concept')
        primary, pp = compiler.compile(Col(column.alias, model._meta.pk))
        predicate, params = predicates[model]
        table = database.ops.quote_name(model._meta.db_table)
        return f'({primary} NOT IN (SELECT "id" FROM {table} WHERE {predicate}))', [*pp, *params]

    for family, data in [('listing', {}), ('search', {'q': 'photography'})]:
        captured = []
        with monkeypatch.context() as patch:
            def capture(query):
                captured.append(query)
                return []
            patch.setattr(proof, 'read_publication_values', capture)
            proof.SQLPublication(discovery.candidates(data), legacy_text=True)
        assert len(captured) == 1
        query = captured[0]
        compiled[(family, 'row')] = query.query.get_compiler(connection=connection).as_sql()
        with monkeypatch.context() as patch:
            patch.setattr(proof.PlainTextProof, 'as_sql', membership)
            compiled[(family, 'set')] = query.query.get_compiler(connection=connection).as_sql()
    assert proof.PlainTextProof.as_sql is original_text
    assert projection.definitions_digest() == fingerprint and projection.supported()
    output = Path(os.environ['TEXT_INDEX_PROBE_OUTPUT'], variant+'.json')
    report = {'variant': variant, 'source_fingerprint': fingerprint, 'stage': 'compiled'}

    def persist():
        output.write_text(json.dumps(report, indent=2)+'\n')

    def read(family, mode, *, read_only=True):
        sql, params = compiled[(family, 'row' if mode == 'row' else 'set')]
        with transaction.atomic(), connection.cursor() as cursor:
            if read_only:
                cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('SET LOCAL jit=off')
            start = time.perf_counter()
            cursor.execute(sql, params)
            executed = time.perf_counter()-start
            start = time.perf_counter()
            rows = cursor.fetchall()
            fetched = time.perf_counter()-start
        return rows, {'execute_seconds': executed, 'fetch_seconds': fetched, 'rows_returned': len(rows)}

    index_present = False
    ddl = []

    def set_indexes(present):
        nonlocal index_present
        if present == index_present:
            return
        start = time.perf_counter()
        with connection.cursor() as cursor:
            for model, name in indexes.items():
                quoted = connection.ops.quote_name(name)
                if present:
                    predicate, params = predicates[model]
                    table = connection.ops.quote_name(model._meta.db_table)
                    cursor.execute(f'CREATE INDEX {quoted} ON {table} ("id") WHERE {predicate}', params)
                else:
                    cursor.execute(f'DROP INDEX {quoted}')
        index_present = present
        ddl.append({'index_present': present, 'seconds': time.perf_counter()-start})

    expected = {f: read(f, 'row')[0] for f in ['listing', 'search']}
    assert all(len(rows)==10000 and all(row[2] is True for row in rows) for rows in expected.values())
    set_indexes(True)
    try:
        # Index maintenance is exercised by actual writes and transaction
        # rollback, not an application-owned validity flag or refresh operation.
        target = Revision.objects.get(pk=expected['listing'][-1][1])
        for field, value in [('description', 'www.example.invalid'), ('description', 'Texto válido 😀'),
                             ('description', 'x'*6001), ('title', '')]:
            with transaction.atomic():
                Revision.objects.filter(pk=target.pk).update(**{field: value})
                old, _ = read('listing', 'row', read_only=False)
                new, _ = read('listing', 'indexed', read_only=False)
                assert new == old and sum(r[2] is True for r in new) == 9999
                transaction.set_rollback(True)
            assert read('listing', 'indexed')[0] == expected['listing']
        rate = Rate.objects.filter(revision=target).first()
        assert rate is not None
        with transaction.atomic():
            Rate.objects.filter(pk=rate.pk).update(concept='')
            old, _ = read('listing', 'row', read_only=False)
            new, _ = read('listing', 'indexed', read_only=False)
            assert new == old and sum(r[2] is True for r in new) == 9999
            transaction.set_rollback(True)
        assert read('listing', 'indexed')[0] == expected['listing']
        report['write_and_rollback_positive_vectors_equal'] = True
        set_indexes(False)
        with connection.cursor() as cursor:
            for table in connection.introspection.table_names():
                cursor.execute('ANALYZE '+connection.ops.quote_name(table))
        before = stats_snapshot()
        samples = []
        orders = [('row', 'set', 'indexed'), ('indexed', 'set', 'row'),
                  ('set', 'indexed', 'row'), ('row', 'indexed', 'set')]
        for pair, order in enumerate(orders):
            for family in ['listing', 'search']:
                for mode in order:
                    set_indexes(mode == 'indexed')
                    # Consistent warmup after DDL, including new index pages;
                    # DDL/warmup are outside all reported SELECT timers.
                    assert read(family, mode)[0] == expected[family]
                    rows, timing = read(family, mode)
                    assert rows == expected[family]
                    samples.append({'pair': pair, 'family': family, 'mode': mode,
                                    'indexes_present': index_present, **timing})
                report.update(stage='controls', samples=samples, ddl_events=ddl)
                persist()
        after = stats_snapshot()
        plans = []
        # Four most relevant reads: both shapes without index, then indexed
        # listing/search. No EXPLAIN inside the paired control sequence.
        for family, mode in [('listing', 'row'), ('listing', 'set'), ('listing', 'indexed'), ('search', 'indexed')]:
            set_indexes(mode == 'indexed')
            sql, params = compiled[(family, 'row' if mode == 'row' else 'set')]
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
                cursor.execute('SET LOCAL jit=off')
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+sql, params)
                plans.append({'family': family, 'mode': mode, 'query_pattern': query_pattern(sql),
                              'plan': redact_plan(cursor.fetchone()[0])})
        with connection.cursor() as cursor:
            sizes = {}
            for name in indexes.values():
                cursor.execute('SELECT pg_relation_size(%s::regclass)', [name])
                sizes[name] = cursor.fetchone()[0]
        medians = {f: {m: statistics.median(s['execute_seconds'] for s in samples if s['family']==f and s['mode']==m)
                      for m in ['row','set','indexed']} for f in ['listing','search']}
        deltas = {}
        for reference in ['row','set']:
            deltas[reference] = [sum(next(s['execute_seconds'] for s in samples if s['pair']==p and s['family']==f and s['mode']==reference)
                        - next(s['execute_seconds'] for s in samples if s['pair']==p and s['family']==f and s['mode']=='indexed')
                        for f in ['listing','search'])/2 for p in range(4)]
        baseline = sum(v['row'] for v in medians.values())/2
        effect = statistics.median(deltas['row']) >= max(.05, .15*baseline) and sum(x>0 for x in deltas['row'])>=3
        index_effect = statistics.median(deltas['set'])>=.05 and sum(x>0 for x in deltas['set'])>=3
        report.update(stage='complete', samples=samples, ddl_events=ddl, sql_execute_medians=medians,
            paired_mean_family_deltas=deltas, material_sql_effect=effect, material_index_effect=index_effect,
            statistics_before=before, statistics_after=after, statistics_endpoints_equal=before==after,
            plans=plans, index_bytes=sizes,
            scope='Real PostgreSQL, own synthetic DB. Prototype only: current row proof vs same sufficient proof grouped in unknown-ID subqueries, without/with partial indexes. Query shape and physical index effects separately compared; data/code/statement binds identical within each case, index DDL intentionally toggled and measured separately. A/B/C orders counterbalanced; each sample has warmup after any DDL; OS/PG caches not reset. Actual updates/rollback outside controls confirm positive-vector equality off-page and native unknown policy inputs. No public route uses the prototype; no cached eligibility or app-maintained validity flag, no normal DB changes. SQL execute includes driver/server/waits/buffering; explicit fetch rows_returned only, not rows_scanned/ORM counts. Normalized statements/plans redact values. Four separate read-only plans after controls, nested plan rows/times not additive. Preserves unknown rather than asserting native ineligibility. This diagnoses an access strategy and does not prove whole-HTTP equivalence/capacity.',
            not_measured=['whole-request effect of prototype', 'common N2/matrix', 'per-rule Python validation',
                'model constructions', 'render', 'DB CPU/RSS/waits/locks/IO', 'rows_affected/scanned',
                'index write overhead under production-like concurrent writes', 'concurrent capacity'])
        persist()
        record_property('text_partial_index_probe', report)
    finally:
        set_indexes(False)
    assert projection.definitions_digest() == fingerprint and projection.supported()
