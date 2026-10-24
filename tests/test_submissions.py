from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import contacts, details, scenario  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import LegalDocument, User
from apps.listings.models import Revision, Submission
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def prepared(request):
    request.getfixturevalue("photo_environment")
    user, person, client = request.getfixturevalue("scenario")
    assert (
        client.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-romantic-1"}
        ).status_code
        == 302
    )
    assert client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 302
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    assert client.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 302
    revision.refresh_from_db()
    assert client.post(f"/es/draft/{revision.pk}/2/", contacts(revision)).status_code == 302
    assert upload(client, revision, raw_image()).status_code == 302
    revision.refresh_from_db()
    return user, person, client, revision


def payload(revision):
    return {"declaration": "on", "edit_version": revision.edit_version}


def test_submission_frozen_idempotent_and_private(prepared):
    user, person, client, revision = prepared
    path = f"/es/draft/{revision.pk}/submit/"
    response = client.post(path, payload(revision))
    assert response.status_code == 302
    assert client.post(path, payload(revision)).status_code == 302
    revision.refresh_from_db()
    assert revision.status == "pending" and Submission.objects.count() == 1
    assert revision.submission.actor_id == user.pk
    assert revision.listing.status == "pending" and not revision.listing.approved_revision_id
    assert client.get(response.url).status_code == 200
    assert b"no se puede editar" in client.get(response.url).content
    assert client.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 409
    photo = Photo.objects.get()
    assert client.post(f"/es/photos/{photo.pk}/remove/").status_code == 409
    assert client.post(f"/es/photos/{photo.pk}/reorder/", {"direction": "up"}).status_code == 409
    assert upload(client, revision, raw_image(seed=2)).status_code == 400
    stranger = User.objects.create_user(
        username="submission-stranger",
        email="stranger@example.invalid",
        email_verified_at=timezone.now(),
    )
    from apps.core.models import LegalAcceptance

    for acceptance in LegalAcceptance.objects.filter(user=user):
        LegalAcceptance.objects.create(
            user=stranger, document=acceptance.document, action=acceptance.action
        )
    other = Client()
    other.force_login(stranger)
    assert other.get(response.url).status_code == 404
    assert other.post(path, payload(revision)).status_code == 404
    assert Client().get(response.url).status_code == 302


@pytest.mark.parametrize(
    "failure",
    [
        "age",
        "consent",
        "photo",
        "phone",
        "legal",
        "catalog",
        "version",
        "declaration",
        "manager_snapshot",
    ],
)
def test_submission_rejects_invalid_or_pending_state(prepared, failure):
    _, person, client, revision = prepared
    data = payload(revision)
    if failure == "age":
        person.age_status = "pending"
        person.save()
    elif failure == "consent":
        person.consent_revoked_at = timezone.now()
        person.save()
    elif failure == "photo":
        Photo.objects.update(comparison_complete=False)
    elif failure == "phone":
        revision.phone = "+34600999888"
        revision.save()
    elif failure == "legal":
        LegalDocument.objects.filter(slug="publishing", language="es").update(active=False)
        LegalDocument.objects.create(
            slug="publishing",
            language="es",
            version="new",
            title="Updated",
            body="Synthetic",
            published_at=timezone.now(),
        )
    elif failure == "catalog":
        revision.categories.update(active=False)
    elif failure == "version":
        data["edit_version"] -= 1
    elif failure == "manager_snapshot":
        person.representationaction_set.update(manager_id="obsolete-manager")
    else:
        data.pop("declaration")
    assert client.post(f"/es/draft/{revision.pk}/submit/", data).status_code == 400
    revision.refresh_from_db()
    assert revision.status == "draft" and not Submission.objects.exists()


def test_submission_csrf_and_concurrent_retry(prepared):
    user, _, client, revision = prepared
    path = f"/es/draft/{revision.pk}/submit/"
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    assert strict.post(path, payload(revision)).status_code == 403
    assert client.get(path).status_code == 405
    barrier = Barrier(2)

    def send():
        close_old_connections()
        try:
            local = Client()
            local.force_login(user)
            barrier.wait(timeout=5)
            return local.post(path, payload(revision)).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(lambda _: send(), range(2))) == [302, 302]
    assert Submission.objects.count() == 1


def test_updated_terms_require_new_acceptance_and_direct_grant(prepared):
    _, person, client, revision = prepared
    LegalDocument.objects.filter(slug="publishing", language="es").update(active=False)
    LegalDocument.objects.create(
        slug="publishing",
        language="es",
        version="new",
        title="Updated",
        body="Synthetic",
        published_at=timezone.now(),
    )
    assert client.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 400
    assert (
        client.post(
            f"/es/draft/{revision.pk}/2/", contacts(revision, legal_version="new")
        ).status_code
        == 302
    )
    revision.refresh_from_db()
    assert client.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 400
    assert (
        client.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "new"}
        ).status_code
        == 302
    )
    assert client.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 302
