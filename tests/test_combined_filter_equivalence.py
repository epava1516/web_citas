"""Native combined-filter membership/order, separate from performance evidence."""

from collections import Counter
from urllib.parse import urlencode

import pytest
from beta_promotional_load_fixture import (
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision

pytestmark = pytest.mark.django_db(transaction=True)


def test_combined_native_filters_match_all_pages_and_pending_reads(request, settings, record_property):
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, 100)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    dataset = redistribute_promotional_geography(dataset, {cities[0]: 70, cities[1]: 30})
    # Explicit test-only attribute distribution; three nonempty pages in the majority city.
    census = {}
    for city, positive in zip(cities, (60, 20), strict=True):
        revisions = list(Revision.objects.filter(approved_for__status='published', municipality_id=city)
                         .order_by('pk'))
        for index, revision in enumerate(revisions):
            revision.profile_type = 'woman' if index < positive else 'man'
            revision.spoken_languages = ['en'] if index < positive else ['fr']
        Revision.objects.bulk_update(revisions, ['profile_type', 'spoken_languages'])
        census[str(city)] = dict(Counter((r.profile_type, tuple(r.spoken_languages)) for r in revisions))
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    rights = set(PromotionEntitlement.objects.values_list('order__listing_id', flat=True))
    cohort = list(Listing.objects.filter(status='published', approved_revision__municipality_id=cities[0],
                                        approved_revision__profile_type='woman').order_by('pk'))
    promoted = next(row for row in cohort if row.pk in rights)
    organic = next(row for row in cohort if row.pk not in rights)
    observations = []
    for phase in ('fresh', 'pending', 'repaired'):
        if phase == 'pending':
            Listing.objects.filter(pk=promoted.pk).update(status='paused')
            Listing.objects.filter(pk=organic.pk).update(status='withdrawn')
        elif phase == 'repaired':
            publication_state.refresh_all()  # Explicit manual repair; no worker credit.
        marks = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
        assert len(marks) == (2 if phase == 'pending' else 0)
        for promotions in (False, True):
            settings.PROMOTION_TEST_MODE = promotions
            for city in cities:
                for text in ('', 'photography', 'absent-combined-token'):
                    native = reference_territorial_order(city, text, promotions=promotions)
                    revisions = {row.pk: row.approved_revision for row in Listing.objects.filter(pk__in=native)
                                 .select_related('approved_revision')}
                    for profile, language in (('woman', 'en'), ('man', 'fr'), ('woman', 'fr')):
                        expected = [pk for pk in native if revisions[pk].profile_type == profile
                                    and language in revisions[pk].spoken_languages]
                        if text != 'absent-combined-token' and (profile, language) != ('woman', 'fr'):
                            assert expected, 'Positive filters must exercise real results'
                        else:
                            assert not expected
                        for locale in ('es', 'en'):
                            seen = []
                            for number in range(1, max(1, (len(expected)+23)//24)+1):
                                data = {'city': city, 'profile': profile, 'language': language,
                                        'q': text, 'page': number}
                                response = client.get('/'+locale+'/?'+urlencode(data))
                                assert response.status_code == 200
                                page = response.context['page']
                                ids = [row.pk for row in page.object_list]
                                assert ids == expected[(number-1)*24:number*24]
                                assert page.paginator.count == len(expected)
                                seen += ids
                                observations.append({'phase': phase, 'promotions': promotions, 'locale': locale,
                                                     'city': city, 'profile': profile, 'language': language,
                                                     'text': text, 'page': number, 'count': len(expected)})
                            assert seen == expected and len(seen) == len(set(seen))
        assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == marks
    assert any(row['page'] == 3 for row in observations)
    record_property('combined_filter_equivalence', {'population': 100, 'rights': 20,
                    'pages_checked': len(observations), 'phases': ['fresh', 'pending', 'repaired'],
                    'pending_marks': 2, 'reads_do_not_repair': True, 'manual_repair': True,
                    'capacity_accepted': False, 'worker_execution_credited': False,
                    'attribute_census': {city: {str(k): v for k, v in counts.items()} for city, counts in census.items()},
                    'observations': observations})
