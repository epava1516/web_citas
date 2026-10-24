"""Observed SQL plans for the experimental pager, not a clean latency benchmark."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from beta_promotion_plans_diagnostic import redact
from beta_promotional_load_fixture import prepare_promotional_load
from beta_set_pager_diagnostic import ORIGINAL, SetPager, candidate
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, publication_state
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_set_pager_observed_plans(request, settings, record_property):
    run_id = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not connection.in_atomic_block
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, 1000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    now = timezone.now()
    results = []

    for text in ['', 'synthetic']:
        observation = {}

        def inspect_order(population, identifier, *, trusted_snapshot):
            assert trusted_snapshot
            with connection.cursor() as cursor:
                cursor.execute('SHOW transaction_isolation')
                assert cursor.fetchone()[0] == 'repeatable read'
                cursor.execute('SHOW transaction_read_only')
                assert cursor.fetchone()[0] == 'on'
            captured = []

            def capture(execute, sql, params, many, context):
                assert not many
                captured.append((sql, params))
                return execute(sql, params, many, context)

            with connection.execute_wrapper(capture):
                original = ORIGINAL(population, identifier, text_search=bool(text), now=now)
                expected = list(original.values_list(identifier, '_promotion_priority')[:24])
                proposed = candidate(population, identifier, text_search=bool(text), now=now)
                assert isinstance(proposed, SetPager)
                actual = proposed[0:24]
            assert expected == actual and len(actual) == 24 and any(p < 2 for _, p in actual)
            assert len(captured) == 3  # rights SELECT, original page SELECT, candidate CTE SELECT
            plans = {}
            for label, (sql, params) in zip(['original_rights', 'original_page', 'candidate_page'], captured):
                with connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) ' + sql, params)
                    raw = cursor.fetchone()[0]
                plans[label] = json.loads(raw) if isinstance(raw, str) else raw
            assert captured[-1][0].lstrip().startswith('WITH live AS MATERIALIZED')
            assert plans['original_rights'][0]['Plan']['Actual Rows'] == 200
            assert plans['original_page'][0]['Plan']['Actual Rows'] == 24
            assert plans['candidate_page'][0]['Plan']['Actual Rows'] == 24
            def nodes(node):
                yield node
                for child in node.get('Plans', []):
                    yield from nodes(child)

            materialized = [node for node in nodes(plans['candidate_page'][0]['Plan'])
                            if node.get('Subplan Name') == 'CTE rights']
            assert len(materialized) == 1
            assert materialized[0]['Actual Loops'] == 1
            assert materialized[0]['Actual Rows'] == 200
            results.append({'route': 'search_en' if text else 'directory_es',
                            'rows_returned': {'original_rights': 200, 'original_page': 24, 'candidate_page': 24},
                            'page_parity': True, 'plans': redact(plans)})
            return proposed

        form = discovery.SearchForm({'q': text})
        assert form.is_valid()
        page = publication_state.state_page(discovery.candidates(form.cleaned_data), 1,
                                           observation=observation, promotion_order=inspect_order)
        assert page and observation['route'] == 'state'
        assert page.paginator.count == 1000 and len(page.object_list) == 24
    assert not PublicationDirty.objects.exists()
    data = {'run_id': run_id, 'result': 'PLANS_COMPLETE_NOT_SPEEDUP', 'profiles': dataset['published'],
            'rights': dataset['promotions']['count'], 'routes': results,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'product_changed': False,
            'limits': ['1000 profiles and 200 rights, not the 10000/2000 capacity cohort',
                       'Observed EXPLAIN ANALYZE executes SELECTs and warms caches; no clean latency ratio',
                       'Node loops/rows are nested and must not be summed as distinct subjects',
                       'Rows returned to client differ; intermediate server work remains in the plan',
                       'No backend CPU, TCP, provider, speedup or adoption verdict']}
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run_id
    (folder / 'beta-set-pager-plans.json').write_text(json.dumps(data, indent=2) + '\n')
    record_property('set_pager_plan_page_parity', True)
    record_property('set_pager_plan_profiles', data['profiles'])
    record_property('set_pager_plan_rights', data['rights'])
