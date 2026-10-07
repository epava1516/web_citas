"""Complete missing decorated-body attribution without repeating the broad profiler."""
import time

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha

from apps.listings import forms as listing_forms
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.benchmark_call_profile import CallProfile
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_individual_text_bodies(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        rows = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += ' ' + suffix
            if row.description_alternative:
                row.description_alternative += ' ' + suffix
            row.telegram = 'bench' + suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'], batch_size=250)
    reports = []
    expected = None
    for mode in ['native', 'projected']:
        with monkeypatch.context() as patch:
            if mode == 'native':
                patch.setattr(projection, 'supported', lambda **kwargs: False)
            profile = CallProfile([listing_forms.validate_listing_text.__wrapped__,
                                   listing_forms.normalize_telegram.__wrapped__])
            patterns = {}
            cache = {}

            def sql_timer(executor, sql, params, many, context):
                if sql not in cache:
                    cache[sql] = query_pattern(sql)
                bucket = patterns.setdefault(cache[sql], {'calls': 0, 'total_time': 0.})
                start = time.perf_counter()
                try:
                    return executor(sql, params, many, context)
                finally:
                    bucket['calls'] += 1
                    bucket['total_time'] += time.perf_counter() - start

            start = time.perf_counter()
            with profile, connection.execute_wrapper(sql_timer):
                response = client.get('/es/')
            elapsed = time.perf_counter() - start
            assert response.status_code == 200
            assert response.context['page'].paginator.count == 10000
            if expected is None:
                expected = response.content
            assert response.content == expected
            route = response.wsgi_request._publication_route
            assert route['route'] == ('projection' if mode == 'projected' else 'fallback')
            rules = profile.report()
            assert {rule['rule'] for rule in rules} == {
                'apps.listings.forms.validate_listing_text', 'apps.listings.forms.normalize_telegram'}
            reports.append({'mode': mode, 'variant': variant, 'count': 10000,
                'request_seconds': elapsed, 'route': route, 'rules': rules,
                'queries': sum(bucket['calls'] for bucket in patterns.values()),
                'sql_execute_seconds': sum(bucket['total_time'] for bucket in patterns.values()),
                'dominant_sql': [{'query_pattern': pattern, **bucket,
                    'mean_time': bucket['total_time'] / bucket['calls']}
                    for pattern, bucket in sorted(patterns.items(),
                                                  key=lambda item: item[1]['total_time'], reverse=True)]})
    record_property('individual_text_profile', reports)
    record_property('scope', 'DjangoClient requests observed with exactly two individual decorated function bodies and identical SQL wrapper in both modes. Outer sensitive-variable wrapper not a target; no callable replacement/unwrap in the semantic fingerprint. Fixed native then projected, shared warm caches, one request each; no unprofiled control or causal overhead/gain estimate. SQL execute excludes fetch/DB CPU; lazy internal overlaps. No rule inputs exported. Broad prior profile retained separately, not combined as one run. Full body/count/page24/route equality here, no other-route or concurrent-capacity acceptance.')
    record_property('not_measured', 'unprofiled_request; causal_overhead; p95_exclusive; materialization; other_rule_metrics; render; rows_returned; rows_affected; rows_scanned; DB_CPU_RSS_IO_waits; capacity')
