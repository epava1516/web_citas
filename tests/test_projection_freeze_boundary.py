"""Memo key semantics must be guarded, including runtime wraps outside page one."""
from functools import wraps

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_semantic_key_wrapper_requires_native_population(request, monkeypatch, record_property):
    client = request.getfixturevalue("directory")
    populate(50)
    ordered = list(candidates({}).values_list("approved_revision_id", flat=True))
    Revision.objects.filter(pk=ordered[25]).update(telegram="a")
    expected = native_ids(candidates({}))
    assert len(expected) == 49 and projection.supported()
    original = projection.freeze
    @wraps(original)
    def collide(value):
        return ("synthetic-key-collision",)
    monkeypatch.setattr(projection, "freeze", collide)
    # Deliberately bypass supported() to reproduce the unsafe proof mechanism.
    context = projection.ProjectedPublication(candidates({}))
    bypass = context.visible_ids(candidates({}))
    assert len(bypass) == 50 and bypass != expected
    assert not projection.supported()
    for language in ["es", "en"]:
        for number in [1, 2, 3]:
            response = client.get(f"/{language}/", {"page": number})
            assert response.status_code == 200
            assert response.context["page"].paginator.count == 49
            assert [row.pk for row in response.context["page"]] == expected[(number-1)*24:number*24]
            assert response.wsgi_request._publication_route["route"] == "fallback"
    record_property("freeze_boundary", {"candidates":50,"native_count":49,
        "unsafe_private_bypass_count":50,"invalid_original_position":25,
        "semantic_wrap_rejected":True,"pages_ES_EN":[1,2,3],
        "public_order_count_pages_match_native":True,
        "scope":"Synthetic PG functional gate; private bypass reproduces collision, public guard preserves native eligibility. No performance/coverage-universal claim."})
