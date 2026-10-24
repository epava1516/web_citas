"""Reject or qualify a history query structure prototype, never product acceptance."""

import hashlib
import json
import os
import statistics
import time
from functools import lru_cache

import pytest
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.promotion_order_models import (
    PromotionEntitlement,
    PromotionOrder,
    PromotionOrderAudit,
    PromotionPaymentAttempt,
    PromotionPaymentEvent,
)
from apps.listings import history, publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible

pytestmark = pytest.mark.django_db(transaction=True)


def test_history_structure_cost(request, settings, monkeypatch, record_property):
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert connection.vendor == 'postgresql' and not connection.in_atomic_block
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    settings.PROMOTION_TEST_MODE = True
    prepare_promotional_load(request, 10)
    listing_id = Listing.objects.filter(status='published').first().pk
    revision_id = Listing.objects.get(pk=listing_id).approved_revision_id
    original = history.rectification_history_ids

    @lru_cache(maxsize=1)
    def structure():
        return original()

    def candidate():
        return structure().all()

    # Exact SQL and parameters, not merely equal counts on an empty history set.
    expected = original().filter(pk=revision_id).query.sql_with_params()
    assert candidate().filter(pk=revision_id).query.sql_with_params() == expected
    first, second = candidate(), candidate()
    assert first is not second and first.query is not second.query
    list(first)
    assert structure()._result_cache is None and second._result_cache is None

    records = []
    for workload in ('history_exists', 'native_visibility'):
        for arm in ('original', 'candidate', 'candidate', 'original',
                    'candidate', 'original', 'original', 'candidate'):
            with monkeypatch.context() as patch:
                patch.setattr(history, 'rectification_history_ids', candidate if arm == 'candidate' else original)
                for _ in range(3):
                    queries = []

                    def sql(execute, statement, params, many, context):
                        queries.append(hashlib.sha256(str(statement).encode()).hexdigest())
                        return execute(statement, params, many, context)

                    started, cpu = time.perf_counter(), time.thread_time()
                    with connection.execute_wrapper(sql):
                        if workload == 'history_exists':
                            value = history.rectification_history_ids().filter(pk=revision_id).exists()
                            assert not value
                        else:
                            listing = Listing.objects.select_related('person', 'approved_revision').get(pk=listing_id)
                            value = publicly_visible(listing)
                            assert value
                    wall, cpu = time.perf_counter() - started, time.thread_time() - cpu
                    records.append({'workload': workload, 'arm': arm, 'wall': wall, 'cpu': cpu,
                                    'queries': queries, 'value': value})
    assert structure()._result_cache is None
    summary = {}
    for workload in ('history_exists', 'native_visibility'):
        rows = [r for r in records if r['workload'] == workload]
        assert all(r['queries'] == rows[0]['queries'] and r['value'] == rows[0]['value'] for r in rows)
        medians = {arm: {clock: statistics.median(r[clock] for r in rows if r['arm'] == arm)
                         for clock in ('wall', 'cpu')} for arm in ('original', 'candidate')}
        summary[workload] = {'medians': medians,
                             'reduction': {clock: 1 - medians['candidate'][clock] / medians['original'][clock]
                                           for clock in ('wall', 'cpu')}}
    eligible = all(value >= .10 for value in summary['native_visibility']['reduction'].values())
    result = {'run': run, 'summary': summary, 'records': records,
              'eligible_for_larger_contrast': eligible, 'product_changed': False,
              'scope': 'Ten profiles, two native rights; SQL/query count parity only for these reads; '
                       'no fresh rectification mutation proof, authorization acceptance, capacity or production ROI; '
                       'shared host/cache, one alternating sequence; candidate not adopted.'}
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run
    (folder / 'history-structure-cost.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('history_structure_cost', json.dumps(result))


@pytest.mark.parametrize(('arm', 'repeat'), [('original', 0), ('candidate', 0),
                                           ('candidate', 1), ('original', 1)])
def test_history_structure_native_preparation(request, settings, monkeypatch, record_property, arm, repeat):
    run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run
    assert connection.vendor == 'postgresql' and not connection.in_atomic_block
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    request.getfixturevalue('directory')  # Same bootstrap policy outside both clocks.
    assert not PromotionOrder.objects.exists() and not PromotionEntitlement.objects.exists()
    original = history.rectification_history_ids

    @lru_cache(maxsize=1)
    def structure():
        return original()

    def candidate():
        return structure().all()

    queries = 0

    def count_sql(execute, statement, params, many, context):
        nonlocal queries
        queries += 1
        return execute(statement, params, many, context)

    with monkeypatch.context() as patch:
        if arm == 'candidate':
            patch.setattr(history, 'rectification_history_ids', candidate)
        started, cpu = time.perf_counter(), time.thread_time()
        with connection.execute_wrapper(count_sql):
            dataset = prepare_promotional_load(request, 1000)
            publication_state.refresh_all()
        wall, cpu = time.perf_counter() - started, time.thread_time() - cpu
    assert dataset['published'] == 1000 and dataset['promotions']['count'] == 200
    assert dataset['promotions']['premium'] == 67 and dataset['promotions']['top'] == 133
    counts = {
        'published': Listing.objects.filter(status='published').count(),
        'paid_orders': PromotionOrder.objects.filter(status='paid', synthetic=True).count(),
        'orders': PromotionOrder.objects.count(), 'rights': PromotionEntitlement.objects.count(),
        'attempts': PromotionPaymentAttempt.objects.filter(status='succeeded').count(),
        'events': PromotionPaymentEvent.objects.filter(outcome='succeeded').count(),
        'audits': PromotionOrderAudit.objects.count(),
    }
    assert counts == {'published': 1000, 'paid_orders': 200, 'orders': 200, 'rights': 200,
                      'attempts': 200, 'events': 200, 'audits': 400}
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    assert arm == 'original' or structure()._result_cache is None
    result = {'run': run, 'arm': arm, 'repeat': repeat, 'wall': wall, 'cpu': cpu,
              'query_count': queries, 'domain_counts': counts,
              'scope': 'Post-bootstrap native preparation and refresh, 1000 profiles/200 rights; '
                       'ABBA repeats share host/cache; no provider, HTTP, capacity or adoption; '
                       'SQL counter overhead unmeasured, repeated fresh cohort IDs/times vary.'}
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run
    (folder / f'history-preparation-{arm}-{repeat}.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('history_native_preparation', json.dumps(result))
