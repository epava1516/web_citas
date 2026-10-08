"""Opt-in diagnosis of SQL predicates and ORM preparation; never a public bypass."""
import json
import os
import statistics
import time
from collections import Counter
from functools import wraps
from pathlib import Path

import pytest
from django.db import connection, transaction
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.query import Query
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('SQL_REMAINING_OUTPUT'), reason='Explicit isolated diagnosis only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_remaining_sql_and_preparation(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        revisions = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, revision in enumerate(revisions):
            suffix = alpha(index)
            revision.description += ' ' + suffix
            if revision.description_alternative:
                revision.description_alternative += ' ' + suffix
            revision.telegram = 'bench' + suffix
        Revision.objects.bulk_update(revisions, ['description', 'description_alternative', 'telegram'], batch_size=250)
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    digest = projection.definitions_digest()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))

    output = Path(os.environ['SQL_REMAINING_OUTPUT'], variant + '.json')
    report = {'variant': variant, 'source_fingerprint': digest, 'count': 10000}

    def persist():
        output.write_text(json.dumps(report, indent=2) + '\n')

    # Capture the actual lazy queryset requested by the production constructor.
    # Suppress only its evaluation, then compile/execute diagnostic statements
    # below. A masked statement NEVER participates in an HTTP request or guard.
    captured, construction = [], []
    for _ in range(3):
        with monkeypatch.context() as patch:
            def capture(query):
                captured.append(query)
                return []
            patch.setattr(proof, 'read_publication_values', capture)
            start = time.perf_counter()
            proof.SQLPublication(discovery.candidates({}))
            construction.append(time.perf_counter() - start)
    assert len(captured) == 3
    query = captured[-1]
    compiled, compilation = {}, {}
    modes = ['full', 'omit_plaintext', 'omit_telegram']
    for mode in modes:
        with monkeypatch.context() as patch:
            if mode != 'full':
                cls = proof.PlainTextProof if mode == 'omit_plaintext' else proof.TelegramProof
                patch.setattr(cls, 'as_sql', lambda *args, **kwargs: ('TRUE', []))
            times = []
            for _ in range(3):
                start = time.perf_counter()
                compiled[mode] = query.query.get_compiler(connection=connection).as_sql()
                times.append(time.perf_counter() - start)
            compilation[mode] = times
    assert projection.definitions_digest() == digest and projection.supported()
    report.update(construction_without_population_evaluation_seconds=construction,
                  standalone_compilation_seconds=compilation, stage='compiled')
    persist()

    def read(mode):
        sql, params = compiled[mode]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('SET LOCAL jit=off')
            start = time.perf_counter()
            cursor.execute(sql, params)
            execute_seconds = time.perf_counter() - start
            start = time.perf_counter()
            rows = cursor.fetchall()
            fetch_seconds = time.perf_counter() - start
        return rows, {'execute_seconds': execute_seconds, 'fetch_seconds': fetch_seconds,
                      'rows_returned': len(rows)}

    expected, _ = read('full')
    assert len(expected) == 10000 and all(row[2] is True for row in expected)
    for mode in modes:
        rows, _ = read(mode)
        assert rows == expected
    before = stats_snapshot()
    samples = []
    orders = [modes, list(reversed(modes)), [modes[1], modes[2], modes[0]], modes]
    for pair, order in enumerate(orders):
        for mode in order:
            rows, sample = read(mode)
            assert rows == expected
            samples.append({'pair': pair, 'mode': mode, **sample})
    report.update(sql_samples=samples, query_patterns={m: query_pattern(q[0]) for m, q in compiled.items()},
                  statistics_before=before, statistics_after=stats_snapshot(), stage='sql_complete')
    persist()

    # Selected method observers leave the native rule callables untouched. Each
    # exclusive value removes only direct instrumented children, exactly once.
    # No global sys.setprofile hook is installed.
    stack, buckets = [], {}

    def observer(name, original):
        @wraps(original)
        def observed(*args, **kwargs):
            current = {'name': name, 'children': Counter(), 'start': time.perf_counter()}
            stack.append(current)
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - current['start']
                assert stack.pop() is current
                exclusive = elapsed - sum(current['children'].values())
                bucket = buckets.setdefault(name, {'calls': 0, 'inclusive_time': 0.,
                    'exclusive_time': 0., 'max_exclusive_time': 0., 'instrumented_children': Counter()})
                bucket['calls'] += 1
                bucket['inclusive_time'] += elapsed
                bucket['exclusive_time'] += exclusive
                bucket['max_exclusive_time'] = max(bucket['max_exclusive_time'], exclusive)
                bucket['instrumented_children'].update(current['children'])
                if stack:
                    stack[-1]['children'][name] += elapsed
        return observed

    expected_body = client.get('/es/').content
    http_samples = []
    for pair, order in enumerate([('plain', 'observed'), ('observed', 'plain')]*2):
        for mode in order:
            buckets, stack = {}, []
            with monkeypatch.context() as patch:
                if mode == 'observed':
                    for owner, name in [(SQLCompiler, 'as_sql'), (Query, 'clone'), (Query, 'add_q')]:
                        patch.setattr(owner, name, observer(owner.__name__ + '.' + name, getattr(owner, name)))
                assert projection.definitions_digest() == digest and projection.supported()
                buckets, stack = {}, []
                start = time.perf_counter()
                response = client.get('/es/')
                total = time.perf_counter() - start
            assert response.status_code == 200 and response.content == expected_body
            route = response.wsgi_request._publication_route
            assert route['route'] == 'projection' and route['candidate_stats']['positive'] == 10000
            assert route['candidate_stats']['native_fallback'] == 0
            assert not route['candidate_stats']['compact_certified_page']
            assert response.context['page'].paginator.count == 10000
            assert not stack and projection.definitions_digest() == digest and projection.supported()
            http_samples.append({'pair': pair, 'mode': mode, 'request_seconds': total, 'route': route,
                'methods': [{'name': k, **v, 'mean_exclusive_time': v['exclusive_time']/v['calls']}
                            for k, v in buckets.items()]})
            report.update(http_samples=http_samples, stage='http_controls')
            persist()
    medians = {m: statistics.median(x['execute_seconds'] for x in samples if x['mode'] == m) for m in modes}
    marginal = {m: [next(x['execute_seconds'] for x in samples if x['mode']=='full' and x['pair']==p)
        - next(x['execute_seconds'] for x in samples if x['mode']==m and x['pair']==p)
        for p in range(4)] for m in modes[1:]}
    report.update(stage='complete', sql_execute_medians=medians, marginal_sql_execute_deltas=marginal,
        statistics_endpoints_equal=report['statistics_before']==report['statistics_after'],
        decision_candidates={m: statistics.median(d)>=.05 and sum(x>0 for x in d)>=3 for m,d in marginal.items()},
        scope='Real isolated PostgreSQL with 10000 known-valid synthetic rows. Captured current complete constructor queryset; construction time includes current-document SQL and excludes population evaluation. Compile separately, no cache changes. Counterfactual predicates are replaced by TRUE ONLY in separately compiled diagnostic reads, never an HTTP route. Matching all-valid outputs does NOT demonstrate equivalence on invalid data or authorize a bypass. Marginal execute deltas include possible plan and evaluation-order changes, not per-regex CPU; not additive. Params/IDs/text absent. Execute excludes explicit fetch; driver may buffer within execute. rows_returned is exactly fetched output tuples of those isolated statements; no rows_scanned inferred. Existing current implementation top5 plans reused from prior reviewed cost evidence. Selected HTTP compiler/query method observer uses nested direct-child subtraction, calls inclusive/exclusive/mean/max; methods are construction, not publication validation. Four plain/observed pairs, body/count/route/fingerprint checked; difference is descriptive, not causal overhead. No actual rule-chain wrapping, no load or capacity result.',
        not_measured=['per-rule publication validation on these HTTP requests', 'model constructions',
            'SQL rows_affected/scanned', 'HTTP SQL rows_returned', 'causal observer overhead',
            'DB CPU/RSS/waits/locks/IO', 'HTTP render in this diagnosis', 'concurrent capacity'])
    persist()
    record_property('remaining_sql_attribution', report)
