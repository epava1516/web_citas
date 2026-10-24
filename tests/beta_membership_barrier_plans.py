"""Compare ordinary and declared-cursor plans of exact membership queries."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from beta_membership_barrier_diagnostic import CANDIDATE, ORIGINAL, barrier_membership
from beta_promotion_plans_diagnostic import redact
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog import promotion_paging
from apps.listings import discovery, publication_state
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def walk(node):
    yield node
    for child in node.get('Plans', []):
        yield from walk(child)


def test_membership_fence_select_and_cursor_plans(request, settings, record_property):
    run_id = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, 1000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    instant = timezone.now()
    routes = []

    for text in ['', 'synthetic']:
        observation = {}

        def inspect_order(population, identifier, *, trusted_snapshot):
            assert trusted_snapshot
            with connection.cursor() as cursor:
                cursor.execute('SHOW transaction_isolation')
                assert cursor.fetchone()[0] == 'repeatable read'
                cursor.execute('SHOW transaction_read_only')
                assert cursor.fetchone()[0] == 'on'
                cursor.execute('SHOW cursor_tuple_fraction')
                fraction = cursor.fetchone()[0]
            rights = promotion_paging.live_entitlements(instant)
            queries = {
                'original': rights.filter(order__listing_id__in=population.order_by().values(identifier)),
                'fence': rights.filter(order__listing_id__in=barrier_membership(population, identifier)),
            }
            ids = [list(q.order_by('pk').values_list('pk', flat=True)) for q in queries.values()]
            assert ids[0] == ids[1] and len(ids[0]) == 200
            ordered = ORIGINAL(population, identifier, text_search=bool(text), now=instant)
            proposed = CANDIDATE(population, identifier, text_search=bool(text), now=instant)
            expected = list(ordered.values_list(identifier, '_promotion_priority')[:24])
            assert list(proposed.values_list(identifier, '_promotion_priority')[:24]) == expected
            plans = {}
            for arm, query in queries.items():
                sql, params = query.values_list('order__listing_id', 'order__kind', 'last_bumped_at').query.sql_with_params()
                plans[arm] = {}
                for mode, prefix in [('select', ''), ('cursor', (
                    'DECLARE beta_membership_plan NO SCROLL CURSOR WITHOUT HOLD FOR '
                ))]:
                    with connection.cursor() as cursor:
                        cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) ' + prefix + sql, params)
                        raw = cursor.fetchone()[0]
                    plan = json.loads(raw) if isinstance(raw, str) else raw
                    assert plan[0]['Plan']['Actual Rows'] == 200
                    authority = [n['Actual Loops'] for n in walk(plan[0]['Plan'])
                                 if n.get('Relation Name') in {'core_agency', 'core_agencymember'}]
                    assert authority
                    plans[arm][mode] = {'plan': redact(plan), 'max_agency_node_loops': max(authority)}
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_cursors WHERE name = 'beta_membership_plan'")
                assert cursor.fetchone()[0] == 0
            original_loops = plans['original']['cursor']['max_agency_node_loops']
            fence_loops = plans['fence']['cursor']['max_agency_node_loops']
            routes.append({'route': 'search' if text else 'directory', 'rights_parity': True,
                           'page_parity': True, 'cursor_tuple_fraction': fraction, 'plans': plans,
                           'cursor_repetition_reduced': original_loops > 200 and fence_loops <= 200})
            return proposed

        form = discovery.SearchForm({'q': text})
        assert form.is_valid()
        page = publication_state.state_page(discovery.candidates(form.cleaned_data), 1,
                                           observation=observation, promotion_order=inspect_order)
        assert page and observation['route'] == 'state'
        assert page.paginator.count == 1000 and len(page.object_list) == 24
    data = {'run_id': run_id, 'result': 'MEMBERSHIP_PLAN_EXPERIMENT_COMPLETE',
            'profiles': dataset['published'], 'rights': dataset['promotions']['count'],
            'routes': routes, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cursor_mechanism_gate': any(r['cursor_repetition_reduced'] for r in routes)
            and all(r['plans']['fence']['cursor']['max_agency_node_loops'] <= 200 for r in routes),
            'product_changed': False,
            'limits': ['Observed plans not clean HTTP latency, backend CPU or TCP capacity',
                       'Original application path streams named cursor500; ordinary SELECT alone is insufficient',
                       'No adoption gate from SELECT improvement without cursor mechanism improvement',
                       '1000 profiles/200 rights, no 10000/2000 extrapolation or real provider',
                       'Plan node loops are not distinct subjects; no GUC/statistics/resource changes']}
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run_id
    (folder / 'beta-membership-barrier-plans.json').write_text(json.dumps(data, indent=2) + '\n')
    record_property('membership_cursor_mechanism_gate', data['cursor_mechanism_gate'])
    record_property('membership_rights_and_page_parity', True)
