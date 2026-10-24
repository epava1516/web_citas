"""Explicit synthetic preparation attribution; no HTTP or capacity acceptance."""

import cProfile
import hashlib
import json
import os
import pstats
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps

import beta_promotional_load_fixture as fixture
import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_promotional_preparation_cost(request, settings, monkeypatch, record_property):
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert not connection.in_atomic_block and not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run
    assert folder.is_dir() and (folder / 'runner.json').is_file()
    stages = defaultdict(lambda: {'calls': 0, 'wall_seconds': 0., 'thread_cpu_seconds': 0.,
                                 'sql_calls': 0, 'sql_execute_seconds': 0.})
    stack = ['other_preparation']

    @contextmanager
    def span(name):
        stack.append(name)
        wall, cpu = time.perf_counter(), time.thread_time()
        try:
            yield
        finally:
            row = stages[name]
            row['wall_seconds'] += time.perf_counter() - wall
            row['thread_cpu_seconds'] += time.thread_time() - cpu
            row['calls'] += 1
            assert stack.pop() == name

    def wrapped(name, original):
        @wraps(original)
        def call(*args, **kwargs):
            with span(name):
                return original(*args, **kwargs)
        return call

    def sql(execute, statement, params, many, context):
        # Count and time only: never retain SQL, parameters, rows or subject IDs.
        row = stages[stack[-1]]
        started = time.perf_counter()
        try:
            return execute(statement, params, many, context)
        finally:
            row['sql_calls'] += 1
            row['sql_execute_seconds'] += time.perf_counter() - started

    profiler = cProfile.Profile()
    started = time.perf_counter()
    with monkeypatch.context() as patch, connection.execute_wrapper(sql):
        for name in ('populate', 'create_order', 'synthetic_event', 'receive_event'):
            patch.setattr(fixture, name, wrapped(name, getattr(fixture, name)))
        profiler.enable()
        try:
            dataset = fixture.prepare_promotional_load(request, 1000)
            with span('refresh_all'):
                publication_state.refresh_all()
        finally:
            profiler.disable()
    elapsed = time.perf_counter() - started
    assert dataset['published'] == 1000 and dataset['promotions']['count'] == 200
    assert Listing.objects.filter(status='published').count() == 1000
    assert PromotionOrder.objects.filter(status='paid', synthetic=True).count() == 200
    assert PromotionOrder.objects.count() == PromotionEntitlement.objects.count() == 200
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    assert stages['populate']['calls'] == stages['refresh_all']['calls'] == 1
    assert all(stages[name]['calls'] == 200 for name in ('create_order', 'synthetic_event', 'receive_event'))
    assert stack == ['other_preparation']
    stats = pstats.Stats(profiler).stats
    functions = []
    root = str(settings.BASE_DIR) + '/'
    for (filename, line, name), (primitive, calls, exclusive, inclusive, _) in stats.items():
        location = filename.removeprefix(root)
        # Dependency filenames are code locations, not request or SQL contents.
        if '/site-packages/' in location:
            location = 'site-packages/' + location.split('/site-packages/', 1)[1]
        functions.append({'file': location, 'line': line, 'function': name,
                          'primitive_calls': primitive, 'calls': calls,
                          'exclusive_seconds': exclusive, 'inclusive_seconds': inclusive})
    result = {
        'run': run, 'profiles': 1000, 'promotional_rights': 200,
        'elapsed_instrumented_seconds': elapsed, 'stages': dict(stages),
        'top_exclusive': sorted(functions, key=lambda row: row['exclusive_seconds'], reverse=True)[:60],
        'top_inclusive': sorted(functions, key=lambda row: row['inclusive_seconds'], reverse=True)[:60],
        'domain_counts_verified': True, 'native_services_preserved': True,
        'scope': 'Instrumented native preparation only, no candidate, HTTP, capacity verdict or measured speedup; '
                 'cProfile uses elapsed function time, not CPU; inclusive rows overlap; SQL timing excludes fetch; '
                 'small cohort cannot establish ten-thousand-profile scaling; overhead unmeasured.',
    }
    (folder / 'preparation-cost.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('preparation_profiles', 1000)
    record_property('preparation_native_rights', 200)
    record_property('preparation_domain_counts_verified', True)
    record_property('preparation_cost', json.dumps(result))


def test_native_authorization_query_attribution(request, settings, monkeypatch, record_property):
    """Small native cohort: query counts by code location, never SQL or values."""
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert connection.vendor == 'postgresql' and not connection.in_atomic_block
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    settings.PROMOTION_TEST_MODE = True
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run
    assert folder.is_dir()
    root = str(settings.BASE_DIR) + '/'
    current = []
    calls = defaultdict(int)
    queries = {}

    def wrapped(name, original):
        @wraps(original)
        def call(*args, **kwargs):
            assert not current
            current.append(name)
            calls[name] += 1
            try:
                return original(*args, **kwargs)
            finally:
                assert current.pop() == name
        return call

    def sql(execute, statement, params, many, context):
        if not current:
            return execute(statement, params, many, context)
        frame = sys._getframe(1)
        locations = []
        while frame is not None:
            filename = frame.f_code.co_filename.removeprefix(root)
            if filename.startswith('apps/'):
                locations.append((filename, frame.f_lineno, frame.f_code.co_name))
            frame = frame.f_back
        del frame
        shape = hashlib.sha256(str(statement).encode()).hexdigest()
        key = (current[-1], shape, tuple(locations))
        row = queries.setdefault(key, {'stage': current[-1], 'query_sha256': shape,
                                      'app_stack': locations, 'calls': 0, 'execute_seconds': 0.})
        started = time.perf_counter()
        try:
            return execute(statement, params, many, context)
        finally:
            row['calls'] += 1
            row['execute_seconds'] += time.perf_counter() - started

    with monkeypatch.context() as patch, connection.execute_wrapper(sql):
        for name in ('create_order', 'receive_event'):
            patch.setattr(fixture, name, wrapped(name, getattr(fixture, name)))
        dataset = fixture.prepare_promotional_load(request, 10)
    assert dataset['published'] == 10 and dataset['promotions']['count'] == 2
    assert dict(calls) == {'create_order': 2, 'receive_event': 2}
    assert PromotionOrder.objects.filter(status='paid', synthetic=True).count() == 2
    assert PromotionOrder.objects.count() == PromotionEntitlement.objects.count() == 2
    assert not current and queries and all(row['execute_seconds'] >= 0 for row in queries.values())
    result = {'run': run, 'profiles': 10, 'native_rights': 2, 'native_calls': dict(calls),
              'queries': sorted(queries.values(), key=lambda row: row['calls'], reverse=True),
              'scope': 'Small native preparation query attribution; query hashes/code locations only; '
                       'no SQL, parameters or rows; stack capture overhead unmeasured; '
                       'no performance comparison, capacity verdict or large-cohort equivalence.'}
    (folder / 'authorization-query-attribution.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('authorization_query_attribution', json.dumps(result))
