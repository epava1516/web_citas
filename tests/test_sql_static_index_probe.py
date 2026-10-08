"""Owned PostgreSQL prototype: distinguish query shape from partial-index effect."""
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models.sql.query import Query
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Revision
from apps.listings.text_proof import IsNotTrueV1
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('STATIC_INDEX_PROBE_OUTPUT'), reason='Explicit owned PostgreSQL prototype only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_static_content_unknown_partial_index_mechanism(request, monkeypatch, record_property, variant):
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
    scalar_names = ["content_language", "profile_type", "time_slot"]
    array_names = ["spoken_languages", "days"]
    static = Q(contact_exposure_accepted=True)
    for name in scalar_names:
        static &= Q(**{name + "__in": [key for key, _ in proof.DetailsForm.base_fields[name].choices]})
    for name in array_names:
        static &= Q(proof.JSONChoicesProof(F(name), [key for key, _ in proof.DetailsForm.base_fields[name].choices]))
    static &= Q(proof.TelegramProof(F("telegram")))
    unknown = Q(IsNotTrueV1(static))
    query = Query(Revision, alias_cols=False)
    where = query.build_where(unknown)
    predicate, params = where.as_sql(query.get_compiler(connection=connection), connection)
    predicates = {Revision: (predicate, params)}
    indexes = {Revision: "probe_static_unknown_revision"}
    original_content = proof.content_proof

    def membership(**kwargs):
        source = original_content(**kwargs)
        assert not source.negated and source.connector == Q.AND
        remaining = Q()
        found = set()
        for child in source.children:
            if isinstance(child, tuple) and child[0] in {"approved_revision__" + n + "__in" for n in scalar_names} | {"approved_revision__contact_exposure_accepted"}:
                found.add(child[0])
                continue
            if isinstance(child, (proof.JSONChoicesProof, proof.TelegramProof)):
                found.add(child.source_expressions[0].name)
                continue
            remaining.children.append(child)
        assert found == {"approved_revision__" + n + "__in" for n in scalar_names} | {"approved_revision__" + n for n in [*array_names, "telegram", "contact_exposure_accepted"]}
        return remaining & ~Q(approved_revision_id__in=Revision.objects.filter(unknown).values("pk"))

    compiled = {}
    for family, data in [("listing", {}), ("search", {"q": "photography"})]:
        for mode in ["row", "set"]:
            captured = []
            with monkeypatch.context() as patch:
                patch.setattr(proof, "read_publication_values", lambda read: captured.append(read) or [])
                if mode == "set":
                    patch.setattr(proof, "content_proof", membership)
                proof.SQLPublication(discovery.candidates(data))
            assert len(captured) == 1
            compiled[family, mode] = captured[0].sql, captured[0].params
    assert proof.content_proof is original_content
    assert projection.definitions_digest() == fingerprint and projection.supported()
    output = Path(os.environ['STATIC_INDEX_PROBE_OUTPUT'], variant+'.json')
    report = {'variant': variant, 'source_fingerprint': fingerprint, 'stage': 'compiled'}

    def persist():
        output.write_text(json.dumps(report, indent=2)+'\n')

    def read(family, mode, *, read_only=True):
        sql, params = compiled[(family, 'row' if mode == 'row' else 'set')]
        with transaction.atomic(), connection.cursor() as cursor:
            if read_only:
                cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout='2000ms'")
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
        for field, value in [
            ("content_language", "xx"), ("profile_type", "unknown"), ("time_slot", "unknown"),
            ("spoken_languages", [["es"]]), ("spoken_languages", [True]),
            ("spoken_languages", ["es", "en", "es"]), ("spoken_languages", "es"),
            ("days", [1]), ("days", []), ("telegram", " @Valid_name "),
            ("telegram", "valid_name\n"), ("telegram", "éxxxx"), ("telegram", "bad!name"),
            ("contact_exposure_accepted", False),
        ]:
            with transaction.atomic():
                Revision.objects.filter(pk=target.pk).update(**{field: value})
                old, _ = read("listing", "row", read_only=False)
                new, _ = read("listing", "indexed", read_only=False)
                assert new == old
                transaction.set_rollback(True)
            assert read("listing", "indexed")[0] == expected["listing"]
        report['write_and_rollback_positive_vectors_equal'] = True
        set_indexes(False)
        with connection.cursor() as cursor:
            for table in connection.introspection.table_names():
                cursor.execute('ANALYZE '+connection.ops.quote_name(table))
        before = stats_snapshot()
        samples = []
        orders = [('row', 'set', 'indexed'), ('indexed', 'set', 'row'),
                  ('set', 'indexed', 'row'), ('row', 'indexed', 'set')]*2
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
                cursor.execute("SET LOCAL statement_timeout='2000ms'")
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
                        for f in ['listing','search'])/2 for p in range(8)]
        baseline = sum(v['row'] for v in medians.values())/2
        effect = statistics.median(deltas['row']) >= max(.05, .15*baseline) and sum(x>0 for x in deltas['row'])>=6
        index_effect = statistics.median(deltas['set'])>=.05 and sum(x>0 for x in deltas['set'])>=6
        report.update(stage='complete', samples=samples, ddl_events=ddl, sql_execute_medians=medians,
            paired_mean_family_deltas=deltas, material_sql_effect=effect, material_index_effect=index_effect,
            statistics_before=before, statistics_after=after, statistics_endpoints_equal=before==after,
            plans=plans, index_bytes=sizes,
            scope='Real PostgreSQL, own synthetic DB. Prototype only: current row proof vs same seven sufficient static-content conditions grouped in an unknown-ID subquery (scalar choices, JSON choices, contact consent, Telegram). Text/catalog/relationships/authority unchanged, without/with partial indexes. Query shape and physical index effects separately compared; data/code/statement binds identical within each case, index DDL intentionally toggled and measured separately. Eight A/B/C orders counterbalanced; each sample has warmup after any DDL; OS/PG caches not reset. Actual updates/rollback outside controls confirm positive-vector equality off-page and native unknown policy inputs. No public route uses the prototype; no cached eligibility or app-maintained validity flag, no normal DB changes. SQL execute includes driver/server/waits/buffering; explicit fetch rows_returned only, not rows_scanned/ORM counts. Normalized statements/plans redact values. Four separate read-only plans after controls, nested plan rows/times not additive. Preserves unknown rather than asserting native ineligibility. This diagnoses an access strategy and does not prove whole-HTTP equivalence/capacity.',
            not_measured=['whole-request effect of prototype', 'common N2/matrix', 'per-rule Python validation',
                'model constructions', 'render', 'DB CPU/RSS/waits/locks/IO', 'rows_affected/scanned',
                'index write overhead under production-like concurrent writes', 'concurrent capacity'])
        persist()
        record_property('static_partial_index_probe', json.dumps(report))
    finally:
        set_indexes(False)
    assert projection.definitions_digest() == fingerprint and projection.supported()
