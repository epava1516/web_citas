"""Synthetic omitted-binary metadata, real PostgreSQL persistence."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityCoverage
from apps.safety.rights_portability_coverage_images import prepare_images, save_images

pytestmark = pytest.mark.django_db(transaction=True)


def test_omitted_image_decisions_replay_remove_and_never_infer_exclusions(
    request, settings, monkeypatch
):
    case, author, _, review, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    reason = "Inspect synthetic omitted images for independent coverage review"
    page = prepare_images(author, case.pk, case.version, review.pk, uuid4(), reason)
    assert page["images"] and page["decisions"] == {}
    photo = page["images"][0]["photo"]
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic fixture exclusion without production factual claim",
        "evidence": "PRIVATE_SYNTHETIC_BINARY_OMISSION",
    }
    key = uuid4()
    row = save_images(author, case.pk, page["token"], key, reason, {photo: facts})
    assert unseal(row.encrypted_coverage)["image_omissions"] == {photo: facts}
    assert save_images(author, case.pk, page["token"], key, reason, {photo: facts}).pk == row.pk
    with pytest.raises(ValidationError):
        save_images(author, case.pk, page["token"], uuid4(), reason, {photo: facts})
    new = prepare_images(author, case.pk, case.version, review.pk, uuid4(), reason)
    assert new["decisions"] == {photo: facts}
    with pytest.raises(ValidationError):
        save_images(author, case.pk, new["token"], uuid4(), reason, {"foreign": facts})
    removed = save_images(author, case.pk, new["token"], uuid4(), reason, {})
    assert unseal(removed.encrypted_coverage)["image_omissions"] == {}
    assert (
        unseal(removed.encrypted_coverage)["omissions"]
        == unseal(row.encrypted_coverage)["omissions"]
    )
    assert RightsPortabilityCoverage.objects.filter(request=case).count() == 2
    case.refresh_from_db()
    assert case.version == row.action.expected_version
