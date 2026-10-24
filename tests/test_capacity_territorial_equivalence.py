"""Large synthetic equivalence; selected HTTP pages, complete native ID census."""

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import verify_territorial_equivalence

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('population', [1000, 10000])
def test_large_territorial_equivalence(request, settings, record_property, population):
    verify_territorial_equivalence(
        request, settings, record_property, population, selected_pages_only=True,
    )
