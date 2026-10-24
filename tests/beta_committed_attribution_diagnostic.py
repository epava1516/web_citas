"""Explicit object/validation counters on the committed synthetic mixture; no TCP."""

import hashlib
import json
import os
import time
from collections import Counter
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

import pytest
from beta_promotional_load_fixture import (
    finalize_promotional_statistics,
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.apps import apps
from django.db import connection
from django.db.models import Model
from mixed_state_plan import native_sponsorships, prepare_committed_mixed_plan
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.listings import discovery, public_validation, publication_state
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('count', [100, 1000, 10000])
def test_committed_attribution(request, settings, monkeypatch, record_property, count):
    run = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    assert run and connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, count)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    dataset = redistribute_promotional_geography(dataset, {cities[0]: count*7//10, cities[1]: count*3//10})
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    plan = prepare_committed_mixed_plan(dataset)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    assert native_sponsorships() == plan['sponsorships']
    finalize_promotional_statistics(dataset | {'published': count-10})
    # All installed application models inherit this method: otherwise a base patch is incomplete.
    assert not [m._meta.label for m in apps.get_models() if 'from_db' in m.__dict__]
    original_descriptor = Model.__dict__['from_db']
    original_from_db = Model.from_db.__func__
    original_validate = public_validation.validate_publication_binding
    original_values = public_validation.read_publication_values
    original_render = discovery.render
    routes = []
    for city in cities:
        for text in ('', 'photography'):
            expected = reference_territorial_order(city, text, promotions=True)
            assert expected == plan['references'][(str(city), text)]
            last = (len(expected)+23)//24
            for number in sorted({1, (last+1)//2, last}):
                for language in ('es', 'en'):
                    routes.append(('/'+language+'/?'+urlencode({'city': city, 'q': text, 'page': number}),
                                   expected, number))
    for pk in (dataset['sample_ids'][0], dataset['sample_ids'][-1]):
        for language in ('es', 'en'):
            routes.append((f'/{language}/listing/{pk}/', None, None))
    assert len(routes) == (24 if count == 100 else 28)
    observations = []
    for path, expected, number in routes:
        def read():
            response = client.get(path)
            assert response.status_code == 200
            if expected is not None:
                page = response.context['page']
                selected = expected[(number-1)*24:number*24]
                assert [row.pk for row in page.object_list] == selected
                assert page.paginator.count == len(expected)
                assert [card['sponsorship'] for card in response.context['cards']] == [
                    plan['sponsorships'].get(pk) for pk in selected]
                assert len(selected) == len(set(selected))
            return len(response.content)

        read()  # Warm request, outside all timed controls and counters.
        controls = []
        for _ in range(5):
            start, cpu = time.perf_counter(), time.process_time()
            size = read()
            controls.append({'wall_seconds': time.perf_counter()-start,
                             'process_cpu_seconds': time.process_time()-cpu, 'bytes': size})
        models, calls, sql, rendering = Counter(), Counter(), [], []
        in_render = False

        def from_db(cls, db, field_names, values):
            result = original_from_db(cls, db, field_names, values)
            models[cls._meta.label] += 1
            return result

        @wraps(original_validate)
        def validate(*args, **kwargs):
            calls['validation_binding_calls'] += 1
            return original_validate(*args, **kwargs)

        @wraps(original_values)
        def values(*args, **kwargs):
            result = original_values(*args, **kwargs)
            calls['publication_values_calls'] += 1
            calls['publication_values_rows'] += len(result)
            return result

        @wraps(original_render)
        def render(*args, **kwargs):
            nonlocal in_render
            assert not in_render
            in_render = True
            start = time.perf_counter()
            try:
                return original_render(*args, **kwargs)
            finally:
                rendering.append(time.perf_counter()-start)
                in_render = False

        def observe(execute, statement, params, many, context):
            start = time.perf_counter()
            phase = 'render' if in_render else 'other'
            try:
                return execute(statement, params, many, context)
            finally:
                sql.append({'seconds': time.perf_counter()-start, 'phase': phase})

        with monkeypatch.context() as patch:
            patch.setattr(Model, 'from_db', classmethod(from_db))
            patch.setattr(public_validation, 'validate_publication_binding', validate)
            patch.setattr(public_validation, 'read_publication_values', values)
            patch.setattr(discovery, 'render', render)
            # Native calibration outside measured windows; then clear the counter.
            if not observations:
                Listing.objects.only('pk').get(pk=dataset['sample_ids'][0])
                assert dict(models) == {'listings.Listing': 1}
                models.clear()
            start, cpu = time.perf_counter(), time.process_time()
            with connection.execute_wrapper(observe):
                size = read()
            measured = {'wall_seconds': time.perf_counter()-start,
                        'process_cpu_seconds': time.process_time()-cpu, 'bytes': size}
        assert Model.__dict__['from_db'] is original_descriptor
        assert public_validation.validate_publication_binding is original_validate
        assert public_validation.read_publication_values is original_values
        assert discovery.render is original_render
        frozen = (dict(models), dict(calls), len(sql), len(rendering))
        read()  # Parity and non-leak control after restoring all patches.
        assert frozen == (dict(models), dict(calls), len(sql), len(rendering))
        assert sql and not in_render
        assert sum(rendering) <= measured['wall_seconds']
        observations.append({'path': path, 'controls': controls, 'instrumented': measured,
                             'models_from_db': dict(models), 'listing_instances': models['listings.Listing'],
                             'other_model_instances': sum(models.values())-models['listings.Listing'],
                             'calls': dict(calls), 'sql': sql, 'sql_calls': len(sql),
                             'sql_driver_seconds': sum(x['seconds'] for x in sql),
                             'render_inclusive_seconds': sum(rendering), 'render_calls': len(rendering),
                             'ordered_ids_sha256': hashlib.sha256('\n'.join(map(str, expected or [])).encode()).hexdigest(),
                             'native_count': None if expected is None else len(expected), 'patches_restored': True})
    assert not PublicationDirty.objects.exists() and native_sponsorships() == plan['sponsorships']
    assert sum(x['calls'].get('validation_binding_calls', 0) for x in observations) > 0
    assert sum(x['calls'].get('publication_values_rows', 0) for x in observations) > 0
    result = {'result': 'COMMITTED_ATTRIBUTION_DIAGNOSTIC_NOT_CAPACITY', 'population': count,
              'visible': count-14, 'rights': count//5, 'active_sponsorships': len(plan['sponsorships']),
              'observations': observations, 'control_requests': len(observations)*5, 'warm_requests': len(observations),
              'instrumented_requests': len(observations), 'post_restore_requests': len(observations),
              'native_parity_and_sponsorship': True, 'dirty_markers_absent': True,
              'capacity_accepted': False, 'worker_execution_credited': False,
              'scope': 'Sequential Django client, two synthetic municipalities. No TCP or concurrency. '
                       'from_db counts ORM instances, not distinct subjects or SQL rows; values/dicts excluded. '
                       'Other models are all non-Listing instances, not proven relation traversals. '
                       'Publication scalar rows counted separately, not added to ORM counts. '
                       'Validation counter counts binding calls, not independent eligibility decisions. '
                       'Render is inclusive; SQL driver is not PostgreSQL CPU. Process CPU includes client/assertions. '
                       'Fixture/oracle excluded. Five controls are descriptive, not SLO percentiles. '
                       'Patches active only for instrumented requests; no causal overhead estimate or speedup claim.'}
    folder = Path(settings.BASE_DIR)/'artifacts/local-ci'/run
    (folder/'beta-committed-attribution.json').write_text(json.dumps(result, indent=2)+'\n')
    record_property('committed_attribution', json.dumps(result))
