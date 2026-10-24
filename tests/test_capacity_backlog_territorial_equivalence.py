"""49 eligible dirty candidates at scale; selected pages, complete native census."""

import pytest
from test_backlog_territorial_equivalence import verify_territorial_unknown49_equivalence
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('population', [1000, 10000])
@pytest.mark.parametrize('with_rights', [False, True], ids=['organic', 'promoted'])
def test_large_territorial_unknown49_equivalence(
        request, settings, record_property, population, with_rights):
    verify_territorial_unknown49_equivalence(
        request, settings, record_property, with_rights,
        population=population, selected_pages_only=True,
    )
