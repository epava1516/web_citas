import hashlib
import io
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import Client
from test_photos import raw_image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.mediafiles.models import Blob, Photo
from apps.safety.crypto import unseal
from apps.safety.models import RightsRectificationProposal
from apps.safety.rectification_photos import source, validate

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic correction of selected photographs with independently reviewable grounds"


def add_source_photo(revision, seed=921):
    from PIL import Image

    raw = raw_image(seed)
    derivative = io.BytesIO()
    Image.open(io.BytesIO(raw)).save(derivative, format="WEBP")
    blob = Blob.objects.create(
        sha256=hashlib.sha256(raw).hexdigest(), status="ready", width=640, height=480
    )
    blob.original.save(f"synthetic-{seed}.jpg", ContentFile(raw), save=False)
    blob.derivative.save(f"synthetic-{seed}.webp", ContentFile(derivative.getvalue()), save=False)
    blob.save()
    return Photo.objects.create(
        revision=revision, blob=blob, position=7, approved=True, comparison_complete=True
    )


@pytest.mark.parametrize("clear", [False, True])
def test_photo_selection_form_rejects_other_sources_and_persists_order(
    request, settings, monkeypatch, clear
):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    add_source_photo(revision)
    before = source(revision)
    assert len(before) == 2
    foreign = (
        Photo.objects.exclude(revision__listing__person=person)
        .filter(removed_at__isnull=True)
        .first()
    )
    assert foreign is not None
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    assert staff.get(path).context["photo_editor"].total_form_count() == 0
    assert str(before[0]).encode() not in staff.get(path).content
    page = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Inspect current photographs before selected correction",
        },
    )
    assert page.status_code == 200
    assert page.context["photo_editor"].total_form_count() == 2
    assert b"Source photo 1" in page.content
    data = initial | {
        "operation": "propose",
        "fields": ["photos"],
        "reason": REASON,
        "photos-TOTAL_FORMS": "2",
        "photos-INITIAL_FORMS": "0",
        "photos-0-photo_id": before[0],
        "photos-0-position": "7",
        "photos-1-photo_id": before[1],
        "photos-1-position": "0",
    }
    for bad in [
        {"photos-1-photo_id": str(foreign.pk)},
        {"photos-1-photo_id": before[0]},
        {"photos-1-position": "7"},
        {"photos-0-position": "8"},
        {"photos-TOTAL_FORMS": "1000000"},
        {"photos-0-photo_id": "invalid"},
    ]:
        assert staff.post(path, data | bad).status_code == 409
    assert (
        staff.post(path, {k: v for k, v in data.items() if k != "photos-TOTAL_FORMS"}).status_code
        == 409
    )
    for bad in [[before[0]] * 2, [str(foreign.pk)], [True], [before[0]] * 9]:
        with pytest.raises(ValidationError):
            validate(bad, person)
    selected = Photo.objects.get(pk=before[1])
    selected.approved = False  # Existing row availability is not permission to publish it.
    selected.save(update_fields=["approved"])
    # The source changed, so the prior explicit audit must be renewed.
    assert staff.post(path, data).status_code == 409
    assert (
        staff.post(
            path,
            initial
            | {
                "operation": "preview",
                "purpose": "Inspect changed approval metadata before correction",
            },
        ).status_code
        == 200
    )
    if clear:
        data.update({"photos-0-DELETE": "on", "photos-1-DELETE": "on"})
    assert not RightsRectificationProposal.objects.exists()
    assert staff.post(path, data).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "photos": [] if clear else list(reversed(before))
    }
    assert source(revision) == before
    assert not revision.photos.filter(removed_at__isnull=False).exists()
    assert not staff.get(path).context["photo_editor"].total_form_count()


def test_photo_bytes_require_current_private_audit_and_scope(request, settings, monkeypatch):
    case, moderator, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    photo = person.listing.approved_revision.photos.filter(removed_at__isnull=True).first()
    foreign = (
        Photo.objects.exclude(revision__listing__person=person)
        .filter(removed_at__isnull=True)
        .first()
    )
    url = f"/en/moderation/rights/{case.pk}/rectification/photos/{photo.pk}/"
    foreign_url = f"/en/moderation/rights/{case.pk}/rectification/photos/{foreign.pk}/"
    assert Client().get(url).status_code == 302
    assert staff.get(url).status_code == 404
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    assert staff.get(url).status_code == 404  # GET form does not authorize bytes.
    assert (
        staff.post(
            path,
            initial
            | {"operation": "preview", "purpose": "Inspect private photo source for correction"},
        ).status_code
        == 200
    )
    response = staff.get(url)
    assert response.status_code == 200 and response["Content-Type"] == "image/webp"
    assert (
        response["Cache-Control"] == "private, no-store"
        and response["X-Robots-Tag"] == "noindex, nofollow"
    )
    assert response["X-Content-Type-Options"] == "nosniff"
    assert b"".join(response.streaming_content)
    response.close()
    assert staff.get(foreign_url).status_code == 404
    assert staff.post(url).status_code == 405
    photo.blob.status = "erasing"
    photo.blob.save(update_fields=["status"])
    assert staff.get(url).status_code == 404
    photo.blob.status = "ready"
    photo.blob.save(update_fields=["status"])
    original_version = case.version
    case.version += 1
    case.save(update_fields=["version"])
    assert staff.get(url).status_code == 404
    case.version = original_version  # Test-only rewind isolates the permission guard.
    case.save(update_fields=["version"])
    from django.contrib.auth.models import Permission

    execute_permission = Permission.objects.get(codename="execute_rights_request")
    moderator.user_permissions.remove(execute_permission)
    assert staff.get(url).status_code == 403
    moderator.user_permissions.add(execute_permission)
    moderator.mfa_version += 1
    moderator.save(update_fields=["mfa_version"])
    denied = staff.get(url)
    assert denied.status_code == 302 and denied.url == "/en/account/mfa/"
    assert denied["Cache-Control"] == "private, no-store"
    assert (
        Client(enforce_csrf_checks=True).post(path, initial | {"operation": "preview"}).status_code
        == 403
    )


def test_photo_selection_rejects_removed_unavailable_and_historical_rows(
    request, settings, monkeypatch
):
    from django.utils import timezone

    from apps.listings.models import Revision

    _, _, _, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    photo = revision.photos.filter(removed_at__isnull=True).first()
    validate([str(photo.pk)], person)
    historical = Revision.objects.create(
        listing=person.listing, manager_version=person.manager_version
    )
    other = Photo.objects.create(revision=historical, blob=photo.blob)
    with pytest.raises(ValidationError):
        validate([str(other.pk)], person)
    photo.removed_at = timezone.now()
    photo.save(update_fields=["removed_at"])
    with pytest.raises(ValidationError):
        validate([str(photo.pk)], person)
    photo.removed_at = None
    photo.save(update_fields=["removed_at"])
    for status in ["queued", "processing", "failed", "erasing", "erased"]:
        photo.blob.status = status
        photo.blob.save(update_fields=["status"])
        with pytest.raises(ValidationError):
            validate([str(photo.pk)], person)
    assert validate([], person) == []
    with pytest.raises(ValidationError):
        validate([str(uuid.uuid4())], person)


def test_unavailable_source_requires_explicit_omission_before_copy(request, settings, monkeypatch):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    photo = person.listing.approved_revision.photos.filter(removed_at__isnull=True).first()
    photo.blob.status = "erased"
    photo.blob.save(update_fields=["status"])
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    assert (
        staff.post(
            path,
            initial
            | {
                "operation": "preview",
                "purpose": "Inspect unavailable image state before deciding correction scope",
            },
        ).status_code
        == 200
    )
    data = initial | {
        "operation": "propose",
        "fields": ["title"],
        "title": "Corrected synthetic title",
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 409
    assert not RightsRectificationProposal.objects.exists()
    omitted = data | {
        "fields": ["title", "photos"],
        "photos-TOTAL_FORMS": "0",
        "photos-INITIAL_FORMS": "0",
    }
    assert staff.post(path, omitted).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "title": "Corrected synthetic title",
        "photos": [],
    }
    photo.refresh_from_db()
    assert photo.removed_at is None  # No physical erasure or source mutation in this fixture.


def test_eight_source_photos_are_editable_and_valid(request, settings, monkeypatch):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    for seed in range(930, 937):
        add_source_photo(revision, seed)
    identifiers = source(revision)
    assert len(identifiers) == 8 and validate(identifiers, person) == identifiers
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Inspect all eight source photographs before corrected order",
        },
    )
    assert page.status_code == 200 and page.context["photo_editor"].total_form_count() == 8
    data = initial | {
        "operation": "propose",
        "fields": ["photos"],
        "reason": REASON,
        "photos-TOTAL_FORMS": "8",
        "photos-INITIAL_FORMS": "0",
    }
    for index, identifier in enumerate(identifiers):
        data.update(
            {f"photos-{index}-photo_id": identifier, f"photos-{index}-position": str(7 - index)}
        )
    assert staff.post(path, data).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "photos": list(reversed(identifiers))
    }
