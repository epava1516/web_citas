import io
import random

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone
from PIL import Image, ImageDraw
from test_drafts import scenario  # noqa: F401

from apps.core.models import Agency, LegalAcceptance, Person, PhoneClaim, User
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Blob, Match, Photo, UploadAttempt


def synthetic_image(seed=1):
    rng = random.Random(seed)
    image = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(image)
    for _ in range(80):
        x, y = rng.randrange(600), rng.randrange(440)
        draw.rectangle((x, y, x + 30, y + 30), fill=tuple(rng.randrange(256) for _ in range(3)))
    return image


def raw_image(seed=1, quality=90):
    output = io.BytesIO()
    image = synthetic_image(seed)
    exif = image.getexif()
    exif[271] = "PRIVATE TEST CAMERA"
    image.save(output, format="JPEG", quality=quality, exif=exif)
    return output.getvalue()


def upload(client, revision, raw):
    return client.post(
        f"/es/draft/{revision.pk}/photos/upload/",
        {"image": SimpleUploadedFile("photo.jpg", raw, content_type="image/jpeg")},
    )


@pytest.fixture
def photo_environment(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "private"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.mark.django_db(transaction=True)
def test_valid_photo_private_derivative_retries_exif_and_remove(request, photo_environment):
    user, person, client = request.getfixturevalue("scenario")
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    raw = raw_image()
    assert upload(client, revision, raw).status_code == 302
    photo = Photo.objects.select_related("blob").get()
    assert photo.blob.status == "ready" and not photo.approved
    with photo.blob.derivative.open("rb") as output:
        image = Image.open(output)
        assert image.format == "WEBP" and not image.getexif() and "exif" not in image.info
    assert upload(client, revision, raw).status_code == 302
    assert Blob.objects.count() == Photo.objects.count() == 1
    assert UploadAttempt.objects.count() == 2
    assert Client().get(f"/es/photos/{photo.pk}/private/").status_code == 302
    response = client.get(f"/es/photos/{photo.pk}/private/")
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    response.close()
    assert Client().get("/private-media/" + photo.blob.original.name).status_code == 404
    assert client.post(f"/es/photos/{photo.pk}/remove/").status_code == 302
    assert client.get(f"/es/photos/{photo.pk}/private/").status_code == 404


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("account_kind", ["individual", "agency"])
def test_duplicate_is_global_without_account_suspension(request, photo_environment, account_kind):
    user, person, client = request.getfixturevalue("scenario")
    client.post(f"/es/person/{person.pk}/listing/start/")
    first = Revision.objects.get()
    assert upload(client, first, raw_image()).status_code == 302
    other = User.objects.create_user(
        username="other-photo",
        email="other-photo@example.invalid",
        email_verified_at=timezone.now(),
    )
    for accepted in LegalAcceptance.objects.filter(user=user):
        LegalAcceptance.objects.create(
            user=other, document=accepted.document, action=accepted.action
        )
    if account_kind == "agency":
        other.role, other.mfa_enabled, other.mfa_version = "agency", True, 1
        other.save(update_fields=["role", "mfa_enabled", "mfa_version"])
        agency = Agency.objects.create(owner=other, name="Synthetic unrelated agency")
        second_person = Person.objects.create(agency=agency, alias="Other")
        claim = PhoneClaim.objects.create(
            agency=agency, phone="+34600555666", verified_at=timezone.now()
        )
    else:
        second_person = Person.objects.create(individual=other, subject=other, alias="Other")
        claim = PhoneClaim.objects.create(
            individual=other, phone="+34600555666", verified_at=timezone.now()
        )
    second_person.phone_claim = claim
    second_person.save(update_fields=["phone_claim"])
    second = Revision.objects.create(
        listing=Listing.objects.create(person=second_person), manager_version=1
    )
    other_client = Client()
    other_client.force_login(other)
    if account_kind == "agency":
        session = other_client.session
        session["mfa_version"] = 1
        session.save()
    assert upload(other_client, second, raw_image()).status_code == 302
    assert Blob.objects.count() == 1 and Photo.objects.count() == 2 and Match.objects.count() == 1
    other.refresh_from_db()
    assert other.is_active
    assert client.get(f"/es/photos/{second.photos.get().pk}/private/").status_code == 404
    assert other_client.post(f"/es/photos/{first.photos.get().pk}/remove/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_invalid_upload_bounds_and_order(request, photo_environment):
    _, person, client = request.getfixturevalue("scenario")
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    assert upload(client, revision, b"<svg>bad</svg>").status_code == 400
    assert upload(client, revision, b"x" * (10 * 1024 * 1024 + 1)).status_code == 400
    assert not Blob.objects.exists()
    for seed in range(8):
        assert upload(client, revision, raw_image(seed)).status_code == 302
    assert upload(client, revision, raw_image(90)).status_code == 400
    photos = list(revision.photos.all())
    assert (
        client.post(f"/es/photos/{photos[-1].pk}/reorder/", {"direction": "up"}).status_code == 302
    )
    assert list(revision.photos.all())[-2].pk == photos[-1].pk


@pytest.mark.django_db(transaction=True)
def test_regional_crop_across_accounts_waits_for_review(request, photo_environment):
    owner, person, client = request.getfixturevalue("scenario")
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    assert upload(client, revision, raw_image(43)).status_code == 302
    other = User.objects.create_user(
        username="cropped", email="cropped@example.invalid", email_verified_at=timezone.now()
    )
    for accepted in LegalAcceptance.objects.filter(user=owner):
        LegalAcceptance.objects.create(
            user=other, document=accepted.document, action=accepted.action
        )
    represented = Person.objects.create(individual=other, subject=other, alias="Crop demo")
    other_revision = Revision.objects.create(
        listing=Listing.objects.create(person=represented), manager_version=1
    )
    other_client = Client()
    other_client.force_login(other)
    output = io.BytesIO()
    synthetic_image(43).crop((128, 0, 640, 480)).save(output, format="JPEG", quality=70)
    assert upload(other_client, other_revision, output.getvalue()).status_code == 302
    photo = other_revision.photos.get()
    assert photo.comparison_complete and photo.matches.filter(method="orb").exists()
    assert not photo.approved and other.is_active
    assert Blob.objects.count() == 2  # Different raw SHA despite visual relation.


@pytest.mark.django_db(transaction=True)
def test_late_photo_is_not_falsely_marked_as_compared(request, photo_environment, monkeypatch):
    from apps.mediafiles import services

    _, person, client = request.getfixturevalue("scenario")
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    upload(client, revision, raw_image(43))
    upload(client, revision, raw_image(44))
    first = revision.photos.order_by("created_at").first()
    late_revision = Revision.objects.create(listing=revision.listing, manager_version=1)
    original = services.compare_signatures
    late = []

    def concurrent_insert(a, b):
        if not late:
            late.append(Photo.objects.create(revision=late_revision, blob=first.blob))
        return original(a, b)

    monkeypatch.setattr(services, "compare_signatures", concurrent_insert)
    services.detect_matches(first.blob_id)
    assert late
    late[0].refresh_from_db()
    assert not late[0].comparison_complete
