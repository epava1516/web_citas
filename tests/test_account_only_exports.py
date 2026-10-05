"""Private own-account snapshots preserve scope and reject stale authority."""

from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_account_linking import account
from test_rights_assignment import action
from test_rights_exports import url
from test_rights_responses import ready

from apps.core.models import Agency, LegalAcceptance, LegalDocument, Person
from apps.listings.models import Favorite, Listing
from apps.mediafiles.models import Photo
from apps.safety.crypto import unseal
from apps.safety.models import RightsImageAccess
from apps.safety.rights_exports import generate
from apps.safety.tasks import purge_expired_exports

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("kind", ["access", "portability"])
@pytest.mark.parametrize("agency", [False, True])
def test_own_account_copy_review_download_and_changed_authority(
    request, settings, monkeypatch, kind, agency
):
    import test_rights_exports

    request.getfixturevalue("directory")
    subject = account()
    if agency:
        owned = Agency.objects.first()
        owned.owner = subject
        owned.save(update_fields=["owner"])
    profiles_before = list(Person.objects.order_by("pk").values())

    def link_account(staff, case, person):
        path, values = action(staff, case, "link")
        return path, values | {"link_account_id": subject.pk}

    monkeypatch.setattr(test_rights_exports, "link", link_account)
    case, actor, staff, public, receipt, _ = ready(request, settings, monkeypatch, kind)
    listing = Listing.objects.first()
    Favorite.objects.create(user=subject, listing=listing)
    LegalAcceptance.objects.create(
        user=subject, document=LegalDocument.objects.first(), action="own_account_fixture"
    )
    path = f"/en/moderation/rights/{case.pk}/export/"
    # Canonical route is checked below by service and receipt; ordinary GET exposes no copy.
    from django.urls import reverse

    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    page = staff.get(path)
    assert page.status_code == 200 and subject.email.encode() not in page.content
    response = staff.post(
        path,
        page.context["form"].initial
        | {"operation": "preview", "purpose": "Read own account source for reviewed copy"},
    )
    assert response.status_code == 200
    source = response.context["source"]
    photo = Photo.objects.first()
    image_path = reverse("rights_image_inspect", kwargs={"case_id": case.pk, "photo_id": photo.pk})
    assert (
        staff.post(
            image_path, {"purpose": "Attempt foreign profile image with account-only authority"}
        ).status_code
        == 404
    )
    assert not RightsImageAccess.objects.filter(request=case).exists()

    assert source["schema"] == "subject-account-copy-v1" and source["request_kind"] == kind
    assert source["subject_account"]["email"] == subject.email
    assert (
        source["profile"] is None and source["representation"] is None and source["revisions"] == []
    )
    assert source["account_activity"]["favorites"] == [
        {
            "listing_reference": str(listing.pk),
            "created_at": Favorite.objects.get(user=subject).created_at.isoformat(),
        }
    ]
    assert [row["action"] for row in source["legal_acceptances"]] == ["own_account_fixture"]
    assert subject.password not in str(source) and "mfa_secret" not in str(source)
    injected = deepcopy(source)
    injected["subject_account"]["email"] = actor.email
    with pytest.raises(ValidationError):
        generate(
            actor,
            case.pk,
            uuid4(),
            case.version,
            "Release own account reviewed partial copy",
            injected,
        )
    extra_favorite = Favorite.objects.create(
        user=subject, listing=Listing.objects.exclude(pk=listing.pk).first()
    )
    with pytest.raises(ValidationError, match="Preview current"):
        generate(
            actor,
            case.pk,
            uuid4(),
            case.version,
            "Release own account reviewed partial copy",
            source,
        )
    extra_favorite.delete()
    key, version = uuid4(), case.version
    export = generate(
        actor, case.pk, key, version, "Release own account reviewed partial copy", source
    )
    assert (
        generate(
            actor, case.pk, key, version, "Release own account reviewed partial copy", source
        ).pk
        == export.pk
    )
    assert export.account_subject_id == subject.pk and export.person_id is None
    assert not export.images.exists() and unseal(export.encrypted_payload)["partial"] is True
    download = url(receipt, export)
    assert Client(enforce_csrf_checks=True).post(download, {"key": uuid4()}).status_code == 403
    response = public.post(download, {"key": uuid4()})
    assert (
        response.status_code == 200 and response.json()["subject_account"]["email"] == subject.email
    )
    assert "rights-account.json" in response["Content-Disposition"]
    assert "no-store" in response["Cache-Control"]
    subject.first_name = "Changed after snapshot"
    subject.save(update_fields=["first_name"])
    assert public.post(download, {"key": uuid4()}).status_code == 404
    assert list(Person.objects.order_by("pk").values()) == profiles_before
    export.expires_at = timezone.now() - timedelta(seconds=1)
    export.save(update_fields=["expires_at"])
    assert purge_expired_exports() == 1
    assert purge_expired_exports() == 0
    export.refresh_from_db()
    assert (
        not export.encrypted_payload
        and export.purged_at
        and export.account_subject_id == subject.pk
    )
    assert public.post(download, {"key": uuid4()}).status_code == 404
    case.refresh_from_db()
    assert case.status == "reviewing"
