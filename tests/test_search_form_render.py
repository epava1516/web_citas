"""The fast select rendering of SearchForm produces Django's exact markup."""

import pytest
from django.utils import translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Category, Municipality, PostalCode, Province, Region, Service, Zone
from apps.listings.discovery import SearchForm

pytestmark = pytest.mark.django_db(transaction=True)


def cases():
    region, province = Region.objects.first(), Province.objects.first()
    city, zone = Municipality.objects.first(), Zone.objects.first()
    postal = PostalCode.objects.first()
    category = Category.objects.first()
    services = [service.pk for service in Service.objects.all()[:2]]
    return [
        None,
        {},
        {"q": 'tag <b>&"quote"'},
        {"profile": ["woman", "trans"], "category": [category.pk], "service": services,
         "services_mode": "all", "region": [region.pk], "province": [province.pk],
         "city": [city.pk], "zone": [zone.pk] if zone else [], "postal_code": [postal.pk] if postal else [],
         "language": ["es", "fr"], "day": ["1", "7"], "time_slot": ["morning"],
         "channel": ["phone", "telegram"], "checked": ["age", "agency"], "reception": "on",
         "travel": "on", "available": "on"},
        {"profile": ["invalid"], "city": ["999999"], "services_mode": "bogus", "day": ["9"]},
    ]


def test_fast_and_template_rendering_are_identical(request):
    request.getfixturevalue("directory")
    category = Category.objects.first()
    category.name_es, category.name_en = 'Fotos <i>&"\'', "Photos <i>&\"'"
    category.save()
    for language in ["es", "en"]:
        with translation.override(language):
            for data in cases():
                english = language == "en"
                fast = SearchForm(data, english=english)
                slow = SearchForm(data, english=english, fast_render=False)
                if data is not None:
                    assert fast.is_valid() == slow.is_valid()
                assert str(fast.as_p()) == str(slow.as_p()), (language, data)
