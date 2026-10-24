"""Explicit detector diagnostic; not ordinary regression or product capacity."""

import inspect

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_prepared_binding import (
    test_prepared_pages_match_native_binding_and_observe_revoked_catalog as prepared_control,
)

from apps.listings import publication_state

pytestmark = pytest.mark.django_db(transaction=True)


def test_dirty_preparation_degradation_is_detected(request, monkeypatch, record_property):
    original = publication_state._state_page
    source = inspect.getsource(original)
    marker = "    dirty = list("
    assert source.count(marker) == 1
    source = source.replace(
        marker,
        """    from apps.catalog.models import Category
    _degraded = not Category.objects.filter(slug="romantic-dating", active=True).exists()
    dirty = list(""",
        1,
    )
    assert source.count("enabled=True") == source.count("prepared_page=True") == 2
    # Runtime copy only: preserve eligibility and warmup, disable preparation
    # exclusively after revocation. PostgreSQL and actual cursors remain real.
    source = source.replace("enabled=True", "enabled=not _degraded")
    source = source.replace("prepared_page=True", "prepared_page=not _degraded")
    namespace = vars(publication_state).copy()
    exec(compile(source, "<dirty-preparation-mutant>", "exec"), namespace)
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "_state_page", namespace["_state_page"])
        with pytest.raises(AssertionError, match="Prepared hydration required for revoked"):
            prepared_control(request, patch, record_property)
    assert publication_state._state_page is original
    record_property(
        "dirty_prepared_mutation_detected",
        {
            "warmup_and_baseline_preserved": True,
            "dirty_cursor_and_context_flags_degraded_together": True,
            "detected_by_independent_prepared_requirement": True,
            "scope": "Detector diagnostic, not functional or capacity acceptance of mutant",
        },
    )
