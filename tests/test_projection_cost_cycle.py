"""Equivalent native/projected events; diverse content is a separate diagnostic."""
import time

import pytest
from django import forms
from django.db import connection, transaction
from django.db.models import Model
from django.db.models.query import ModelIterable, prefetch_one_level
from django.db.models.signals import post_init
from django.utils.functional import SimpleLazyObject
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, submissions
from apps.listings import forms as listing_forms
from apps.listings import projected_publication as projection
from apps.listings.forms import ContactsForm, DetailsForm, RateForm
from apps.listings.models import Revision
from apps.listings.public_validation import (
    PublicationContext,
    SnapshotDetails,
    validate_publication_binding,
    memoize_publication_field_clean,
)
from scripts.benchmark_call_profile import CallProfile
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def targets():
    functions = [projection.definitions_digest, projection.projected_page,
                 moderation.validate_submission, moderation.publicly_visible,
                 submissions.publication_ready, discovery.render, Model.from_db,
                 ModelIterable.__iter__, prefetch_one_level,
                 validate_publication_binding, SimpleLazyObject._setup,
                 memoize_publication_field_clean, listing_forms.validate_details_values,
                 listing_forms.validate_listing_text.__wrapped__,
                 listing_forms.normalize_telegram.__wrapped__]
    for cls in [projection.ProjectedPublication, PublicationContext, SnapshotDetails,
                DetailsForm, ContactsForm, RateForm, Revision, forms.Field]:
        for name in ['__init__', 'full_clean', 'clean', '_clean_fields', '_clean_form',
                     '_post_clean', 'clean_fields', 'run_validators', 'validate',
                     'positive', 'authority', 'native_content', 'visible_ids',
                     'details', 'details_valid', 'contacts_valid', 'rate_valid']:
            function = getattr(cls, name, None)
            if callable(function) and hasattr(function, '__code__'):
                functions.append(function)
    return functions


def alpha(index):
    text = ''
    for _ in range(4):
        text = chr(97 + index % 26) + text
        index //= 26
    return text


@pytest.mark.parametrize('count,variant', [(10000, 'contractual'), (100, 'contractual'),
                                         (1000, 'contractual'), (10000, 'diverse')])
def test_projection_comparable_cycle(request, monkeypatch, record_property, count, variant):
    client = request.getfixturevalue('directory')
    populate(count)
    assert connection.vendor == 'postgresql' and projection.supported()
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
    explain_candidates = []
    expected = None
    for mode in ['native', 'projected']:
        with monkeypatch.context() as patch:
            if mode == 'native':
                patch.setattr(projection, 'supported', lambda **kwargs: False)
            started = time.perf_counter()
            control = client.get('/es/')
            control_seconds = time.perf_counter() - started
            assert control.status_code == 200
            assert control.context['page'].paginator.count == count
            if expected is None:
                expected = control.content
            assert control.content == expected
            profile = CallProfile(targets())
            patterns = {}
            sql_seconds = 0.
            queries = 0
            normalization_cache = {}
            read_queries = {}

            def sql_timer(execute, sql, params, many, context):
                nonlocal sql_seconds, queries
                queries += 1
                if sql not in normalization_cache:
                    normalization_cache[sql] = query_pattern(sql)
                pattern = normalization_cache[sql]
                if sql.lstrip().upper().startswith("SELECT"):
                    read_queries.setdefault(pattern, (sql, params))
                bucket = patterns.setdefault(pattern, {'calls': 0, 'total_time': 0.})
                started = time.perf_counter()
                try:
                    return execute(sql, params, many, context)
                finally:
                    elapsed = time.perf_counter() - started
                    sql_seconds += elapsed
                    bucket['calls'] += 1
                    bucket['total_time'] += elapsed

            post_init.connect(profile.objects, weak=False)
            try:
                started = time.perf_counter()
                with profile, connection.execute_wrapper(sql_timer):
                    measured = client.get('/es/')
                total = time.perf_counter() - started
            finally:
                post_init.disconnect(profile.objects)
            assert measured.content == control.content
            assert measured.wsgi_request._publication_route == control.wsgi_request._publication_route
            route = measured.wsgi_request._publication_route
            assert route['route'] == ('projection' if mode == 'projected' else 'fallback')
            if mode == 'projected':
                assert profile.projection_stats[0]['positive'] == count
                assert profile.projection_stats[0]['native_fallback'] == 0
            reports.append({'mode': mode, 'variant': variant, 'count': count,
                'queries': queries, 'sql_execute_seconds': sql_seconds,
                'request_seconds': total, 'control_request_seconds': control_seconds,
                'paired_difference_seconds': total - control_seconds,
                'route': route, 'projection_stats': profile.projection_stats,
                'objects': dict(profile.materialized), 'objects_provenance': dict(profile.provenance),
                'rules': profile.report(),
                'dominant_sql': [{'query_pattern': pattern, **bucket,
                    'mean_time': bucket['total_time'] / bucket['calls']}
                    for pattern, bucket in sorted(patterns.items(),
                                                  key=lambda item: item[1]['total_time'], reverse=True)]})
            if sql_seconds >= 0.50 * total:
                dominant = max(read_queries, key=lambda pattern: patterns[pattern]['total_time'])
                explain_candidates.append((mode, dominant, read_queries[dominant]))
    plans = []

    def redact_plan(value):
        if isinstance(value, dict):
            return {key: redact_plan(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact_plan(item) for item in value]
        if isinstance(value, str):
            return query_pattern(value)
        return value

    # Separate reads after both measured modes. No timer/profile incorporates
    # EXPLAIN; plans can warm caches, so never execute them between paired modes.
    for mode, pattern, (sql, params) in explain_candidates:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
            plans.append({'mode': mode, 'query_pattern': pattern,
                          'plan': redact_plan(cursor.fetchone()[0])})
    record_property('separate_explain', {'threshold': 'SQL execute >=50% instrumented request is a diagnostic dominance heuristic, not an SLO', 'plans': plans, 'scope': 'Owned synthetic PG read-only SELECT, after both measured requests. Plan actual rows are per-node stream counts with loops, not ORM objects or inferred rows_scanned/request; no statement parameters stored. OS/PG caches warmed, not reset.'})
    record_property('cycle', reports)
    record_property('scope', 'DjangoClient end-to-end excludes fixtures/network/Gunicorn; synchronous sys.setprofile call/return events do not alter native callable chains. Exclusive discounts only direct observed children once; inline/unobserved work remains inside parent. Generator iteration events are yield segments, not unique objects. SQL execute excludes fetch; lazy SQL may overlap validation, hydration, render. Model post_init counts constructions including transient objects, not unique entities or SQL rows. Shared binding, lazy setup, field memo installation and explicit content/telegram value rules are directly observed in BOTH modes; memo hit closure itself is not a separate target. Text/Telegram targets are the explicitly selected decorated bodies; their outer sensitive-variable wrappers are unobserved. This observer selection does not unwrap or weaken the security fingerprint, which still checks all callable layers. Shared code with different labels is rejected. Child attribution differs from historical profiles without these targets, so exclusive values are not identical instruments across those sources. Seconds; thread CPU only this thread. Native then projected, control then observed, shared warmed OS/PG caches, no reset; one sample each, paired difference is not causal overhead. Validity gate requires native full-population count, HTTP body and page24 equivalence; no real data or capacity claim.')
    record_property('not_measured', 'rows_returned; rows_affected; rows_scanned; DB CPU; RSS; waits; locks; IO; causal overhead; p95 exclusive; concurrent capacity')
