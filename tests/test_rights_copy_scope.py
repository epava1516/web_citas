import json
import uuid

import pytest
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared, url

from apps.core.models import LegalAcceptance, Person, PhoneClaim, User
from apps.safety.models import RightsExport
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


def test_account_projection_is_subject_only_redactable_and_never_contains_secrets(
    request, settings
):
    case, user, _, client, receipt, person = prepared(request, settings)
    subject = person.subject
    subject.first_name, subject.last_name = "Synthetic Given", "Synthetic Family"
    subject.save(update_fields=["first_name", "last_name"])
    source = preview(
        user, case.pk, case.version, "Review subject account and profile data before release"
    )
    assert source["schema"] == "subject-profile-copy-v2"
    assert source["subject_account"]["email"] == subject.email
    assert source["subject_account"]["first_name"] == "Synthetic Given"
    assert len(source["legal_acceptances"]) == LegalAcceptance.objects.filter(user=subject).count()
    forbidden = [
        subject.password,
        person.agency.owner.email,
        "mfa_secret_encrypted",
        "session_version",
        "recovery_digest",
        "token",
        "digest",
    ]
    serialized = json.dumps(source)
    assert all(value not in serialized for value in forbidden)
    foreign = json.loads(serialized)
    foreign["subject_account"]["email"] = person.agency.owner.email
    with pytest.raises(ValidationError):
        generate(user, case.pk, uuid.uuid4(), case.version, "Release scoped account copy", foreign)
    source["subject_account"]["last_name"] = ""
    export = generate(
        user, case.pk, uuid.uuid4(), case.version, "Release redacted subject account copy", source
    )
    copy = client.post(url(receipt, export), {"key": uuid.uuid4()}).json()
    assert copy["subject_account"]["last_name"] == "" and copy["partial"]
    assert person.agency.owner.email not in json.dumps(copy)


def test_subject_account_and_image_inventory_drift_requires_new_preview(request, settings):
    case, user, _, _, _, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Inspect source before generating a current private copy"
    )
    User.objects.filter(pk=person.subject_id).update(first_name="Account changed after preview")
    with pytest.raises(ValidationError):
        generate(user, case.pk, uuid.uuid4(), case.version, "Release stale account copy", source)
    source = preview(user, case.pk, case.version, "Inspect updated account and image inventory")
    photo = person.listing.revisions.first().photos.first()
    assert photo and source["revisions"][0]["images"]
    assert all(
        not item["content_included"]
        for revision in source["revisions"]
        for item in revision["images"]
    )
    photo.position += 1
    photo.save(update_fields=["position"])
    with pytest.raises(ValidationError):
        generate(
            user, case.pk, uuid.uuid4(), case.version, "Release stale image inventory copy", source
        )
    assert not RightsExport.objects.exists()


def test_shared_contact_is_withheld_and_personal_claim_can_be_redacted(request, settings):
    case, user, _, _, _, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Inspect shared publication contacts before disclosure"
    )
    assert all(item["contacts"]["phone"] == "" for item in source["revisions"])
    assert all(item["contacts"]["telegram"] == "" for item in source["revisions"])
    revision = person.listing.revisions.first()
    # Scoped synthetic ownership fixture; this is not real telephone verification.
    claim = PhoneClaim.objects.get(phone=revision.phone)
    claim.agency = None
    claim.individual = person.subject
    claim.save()
    person.phone_claim = claim
    person.save(update_fields=["phone_claim"])
    source = preview(
        user, case.pk, case.version, "Inspect explicitly subject-owned contact for private copy"
    )
    assert source["revisions"][0]["contacts"]["phone"] == revision.phone
    source["revisions"][0]["contacts"]["phone"] = ""
    source["revisions"][0]["contacts"]["whatsapp"] = False
    generate(user, case.pk, uuid.uuid4(), case.version, "Release copy with contact removed", source)


def test_missing_subject_never_substitutes_agency_owner_or_requester(request):
    from apps.safety.rights_copy_data import subject_data

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    person.subject = None
    result = subject_data(person)
    assert result["subject_account"] is None and not result["legal_acceptances"]
    assert person.agency.owner.email not in json.dumps(result)
    assert not result["representation"]["verifications"]


def test_favorites_projection_is_own_activity_and_drift_blocks_stale_copy(request, settings):
    from apps.listings.models import Favorite

    case, user, _, client, receipt, person = prepared(request, settings)
    owner = person.agency.owner
    own = Favorite.objects.create(user=person.subject, listing=person.listing)
    Favorite.objects.create(user=owner, listing=person.listing)
    source = preview(
        user, case.pk, case.version, "Inspect subject favorite activity before release"
    )
    assert source["account_activity"]["favorites"] == [
        {"listing_reference": str(own.listing_id), "created_at": own.created_at.isoformat()}
    ]
    assert owner.email not in json.dumps(source["account_activity"])
    own.delete()
    with pytest.raises(ValidationError):
        generate(
            user, case.pk, uuid.uuid4(), case.version, "Release stale subject favorite copy", source
        )
    source = preview(user, case.pk, case.version, "Inspect refreshed subject favorite activity")
    assert source["account_activity"]["favorites"] == []
    export = generate(
        user, case.pk, uuid.uuid4(), case.version, "Release reviewed subject favorite copy", source
    )
    assert (
        client.post(url(receipt, export), {"key": uuid.uuid4()}).json()["account_activity"]
        == source["account_activity"]
    )
