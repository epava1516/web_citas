"""Separate controls and SQL/render observation for native combined-filter cases."""

import hashlib
import json
import os
import time
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

import pytest
from beta_promotional_load_fixture import (
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_exposure import eligible
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import discovery, publication_state
from apps.listings.models import Listing, PublicationDirty, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('count', [100, 1000, 10000])
def test_combined_filter_cost(request, settings, monkeypatch, record_property, count):
    run = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    assert run and connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, count)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    redistribute_promotional_geography(dataset, {cities[0]: count*7//10, cities[1]: count*3//10})
    for city, positive in zip(cities, (count*6//10, count*2//10), strict=True):
        revisions = list(Revision.objects.filter(approved_for__status='published', municipality_id=city)
                         .order_by('pk'))
        for index, revision in enumerate(revisions):
            revision.profile_type = 'woman' if index < positive else 'man'
            revision.spoken_languages = ['en'] if index < positive else ['fr']
        Revision.objects.bulk_update(revisions, ['profile_type', 'spoken_languages'])
    publication_state.refresh_all()
    rights = set(PromotionEntitlement.objects.values_list('order__listing_id', flat=True))
    cohort = list(Listing.objects.filter(status='published', approved_revision__municipality_id=cities[0],
                                        approved_revision__profile_type='woman').order_by('pk'))
    promoted = next(row for row in cohort if row.pk in rights)
    organic = next(row for row in cohort if row.pk not in rights)
    observations = []
    for phase in ('fresh', 'pending'):
        if phase == 'pending':
            Listing.objects.filter(pk=promoted.pk).update(status='paused')
            Listing.objects.filter(pk=organic.pk).update(status='withdrawn')
        marks = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
        assert len(marks) == (2 if phase == 'pending' else 0)
        for promotions in (False, True):
            settings.PROMOTION_TEST_MODE = promotions
            # Recomputed for each state/mode, never measured as request work or cached across mutations.
            sponsors = {}
            if promotions:
                native_rights = list(PromotionEntitlement.objects.select_related('order'))
                assert len(native_rights) == count//5
                native_listings = {row.pk: row for row in Listing.objects.filter(
                    pk__in=[r.order.listing_id for r in native_rights])}
                now = timezone.now()
                for right in native_rights:
                    assert right.order.synthetic and right.order.kind in {'top', 'premium'}
                    if eligible(right, native_listings[right.order.listing_id], now):
                        sponsors[right.order.listing_id] = right.order.kind
            references = {city: reference_territorial_order(city, 'photography', promotions=promotions)
                          for city in cities}
            revisions = {row.pk: row.approved_revision for row in Listing.objects.filter(status='published')
                         .select_related('approved_revision')}
            majority_count = sum(revisions[pk].profile_type == 'woman'
                                 and 'en' in revisions[pk].spoken_languages for pk in references[cities[0]])
            last_page = (majority_count+23)//24
            selected_pages = (1, (last_page+1)//2, last_page)
            assert len(set(selected_pages)) == 3
            specs = [(cities[0], 'woman', 'en', page) for page in selected_pages] + [
                (cities[1], 'woman', 'en', 1), (cities[0], 'man', 'fr', 1),
                (cities[0], 'woman', 'fr', 1)]
            for city, profile, language, number in specs:
                expected = [pk for pk in references[city] if revisions[pk].profile_type == profile
                            and language in revisions[pk].spoken_languages]
                assert bool(expected) == ((profile, language) != ('woman', 'fr'))
                selected = expected[(number-1)*24:number*24]
                labels = [sponsors.get(pk) for pk in selected]
                digest = hashlib.sha256('\n'.join(map(str, selected)).encode()).hexdigest()
                for locale in ('es', 'en'):
                    path = '/'+locale+'/?'+urlencode({'city': city, 'profile': profile, 'language': language,
                                                     'q': 'photography', 'page': number})

                    def read():
                        response = client.get(path)
                        assert response.status_code == 200
                        page = response.context['page']
                        assert [row.pk for row in page.object_list] == selected
                        assert page.paginator.count == len(expected)
                        assert [card['sponsorship'] for card in response.context['cards']] == labels
                        return len(response.content)

                    read()  # Warm observation, distinct from five uninstrumented controls.
                    controls = []
                    for _ in range(5):
                        start, cpu = time.perf_counter(), time.process_time()
                        size = read()
                        controls.append({'wall_seconds': time.perf_counter()-start,
                                         'process_cpu_seconds': time.process_time()-cpu, 'bytes': size})
                    sql, rendering = [], []
                    in_render = False
                    original_render = discovery.render

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
                        phase_name = 'render' if in_render else 'other'
                        try:
                            return execute(statement, params, many, context)
                        finally:
                            sql.append({'seconds': time.perf_counter()-start, 'phase': phase_name})

                    with monkeypatch.context() as patch:
                        patch.setattr(discovery, 'render', render)
                        start, cpu = time.perf_counter(), time.process_time()
                        with connection.execute_wrapper(observe):
                            size = read()
                        instrumented = {'wall_seconds': time.perf_counter()-start,
                                        'process_cpu_seconds': time.process_time()-cpu, 'bytes': size}
                    assert len(rendering) == 1 and sql and not in_render
                    assert sum(rendering) <= instrumented['wall_seconds']
                    observations.append({'phase': phase, 'promotions': promotions, 'locale': locale,
                                         'city': city, 'profile': profile, 'language': language, 'page': number,
                                         'native_count': len(expected), 'returned': len(selected),
                                         'selected_majority_pages': selected_pages,
                                         'ordered_ids_sha256': digest, 'sponsorship': labels,
                                         'controls': controls, 'instrumented': instrumented,
                                         'render_inclusive_seconds': rendering[0], 'sql': sql,
                                         'sql_calls': len(sql), 'sql_driver_seconds': sum(x['seconds'] for x in sql)})
        assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == marks
    assert len(observations) == 48
    result = {'result': 'COMBINED_FILTER_DIAGNOSTIC_NOT_CAPACITY', 'population': count, 'rights': count//5,
              'observations': observations, 'control_requests': 240, 'instrumented_requests': 48,
              'warm_requests': 48, 'native_parity_and_sponsorship': True, 'dirty_generations_unchanged': True,
              'worker_execution_credited': False, 'capacity_accepted': False,
              'scope': 'Sequential Django client; synthetic two municipalities and attributes; no TCP or concurrency. '
                       'Fixture/native oracle outside measured windows; warm and five controls separate from one instrumented request. '
                       'Render inclusive includes driver/waits; SQL driver duration is not PostgreSQL CPU. '
                       'Process CPU covers pytest/client and assertions; no per-service attribution or causal instrumentation estimate. '
                       'Five controls provide descriptive samples, not reliable SLO percentiles. No SQL text, parameters or subject data.'}
    folder = Path(settings.BASE_DIR)/'artifacts/local-ci'/run
    (folder/'beta-combined-filter-cost.json').write_text(json.dumps(result, indent=2)+'\n')
    record_property('combined_filter_cost', json.dumps(result))
