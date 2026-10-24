"""Complete native mixed-state census, selected HTTP pages at explicit scales."""

import pytest
from test_discovery import directory  # noqa: F401
from test_mixed_state_territorial_equivalence import verify_mixed_state_territorial_equivalence
from test_photos import photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('population', [1000, 10000])
def test_large_mixed_state_territorial_equivalence(request, settings, record_property, tmp_path, population):
    verify_mixed_state_territorial_equivalence(
        request, settings, record_property, tmp_path, 'manual',
        population=population, selected_pages_only=True,
    )
