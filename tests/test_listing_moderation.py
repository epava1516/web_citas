from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import payload, prepared  # noqa: F401

from apps.core.models import LegalAcceptance, Person, User
from apps.listings.models import Listing, ModerationDecision, Revision
from apps.mediafiles.models import Match, Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def pending(request):
    owner, person, client, revision = request.getfixturevalue("prepared")
    assert client.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 302
    moderator = User.objects.create_user(
        username="listing-moderator",
        email="listing-moderator@example.invalid",
        password="Long-moderator-password!847",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    moderator.user_permissions.add(Permission.objects.get(codename="review_listing"))
    for acceptance in LegalAcceptance.objects.filter(
        user=owner, action__in=["account_terms", "privacy_notice"]
    ):
        LegalAcceptance.objects.create(
            user=moderator, document=acceptance.document, action=acceptance.action
        )
    reviewer = Client()
    reviewer.force_login(moderator)
    session = reviewer.session
    session["mfa_version"] = 1
    session.save()
    return person, client, revision, moderator, reviewer


def decision(revision, **changes):
    return {
        "edit_version": revision.edit_version,
        "outcome": "approved",
        "reason": "Contenido sintético y autorización revisados",
        **changes,
    }


def test_approval_exposes_exact_revision_and_only_derivative(pending):
    person, owner, revision, _, reviewer = pending
    public = Client()
    path = f"/es/listing/{revision.listing_id}/"
    photo = Photo.objects.get(revision=revision)
    image_path = path + f"photo/{photo.pk}/"
    assert public.get(path).status_code == public.get(image_path).status_code == 404
    assert reviewer.get(f"/es/moderation/photos/{photo.pk}/").status_code == 200
    response = reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision))
    assert response.status_code == 302, response.content
    revision.refresh_from_db()
    listing = Listing.objects.get()
    assert listing.approved_revision_id == revision.pk and revision.status == "approved"
    assert listing.expires_at > timezone.now() and ModerationDecision.objects.count() == 1
    assert revision.title.encode() in public.get(path).content
    assert person.subject.email.encode() not in public.get(path).content
    image = public.get(image_path)
    assert image.status_code == 200 and image["Content-Type"] == "image/webp"
    image.close()
    assert public.get(f"/es/photos/{photo.pk}/private/").status_code == 302
    assert public.get("/private-media/" + photo.blob.original.name).status_code == 404
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 400
    )
    assert ModerationDecision.objects.count() == 1
    assert owner.post(f"/es/person/{person.pk}/revoke/").status_code == 302
    assert public.get(path).status_code == public.get(image_path).status_code == 404


@pytest.mark.parametrize("condition", ["consent", "age", "matches", "version"])
def test_approval_revalidates_current_prerequisites(pending, condition):
    person, _, revision, _, reviewer = pending
    data = decision(revision)
    if condition == "consent":
        person.consent_revoked_at = timezone.now()
        person.save()
    elif condition == "age":
        person.age_status = "failed"
        person.save()
    elif condition == "version":
        data["edit_version"] -= 1
    else:
        other = User.objects.create_user(username="other-person", email="other@example.invalid")
        duplicate_person = Person.objects.create(individual=other, alias="Synthetic duplicate")
        duplicate_revision = Revision.objects.create(
            listing=Listing.objects.create(person=duplicate_person), manager_version=1
        )
        photo = Photo.objects.get(revision=revision)
        candidate = Photo.objects.create(revision=duplicate_revision, blob=photo.blob)
        Match.objects.create(photo=candidate, candidate=photo, method="sha256")
    assert reviewer.post(f"/es/moderation/listings/{revision.pk}/", data).status_code == 400
    revision.refresh_from_db()
    assert revision.status == "pending" and not ModerationDecision.objects.exists()
    assert not revision.listing.approved_revision_id


def test_permission_mfa_self_review_rejection_and_concurrency(pending):
    person, owner, revision, moderator, reviewer = pending
    path = f"/es/moderation/listings/{revision.pk}/"
    assert owner.get(path).status_code == 403
    assert Client().get(path).status_code == 302
    person.subject = moderator
    person.save()
    assert reviewer.post(path, decision(revision)).status_code == 403
    person.subject = person.individual
    person.save()
    barrier = Barrier(2)

    def reject():
        close_old_connections()
        try:
            local = Client()
            local.force_login(moderator)
            session = local.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return local.post(
                path, decision(revision, outcome="rejected", reason="Corrección necesaria")
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: reject(), range(2))) == [302, 400]
    revision.refresh_from_db()
    assert revision.status == "rejected" and ModerationDecision.objects.count() == 1
    assert Client().get(f"/es/listing/{revision.listing_id}/").status_code == 404
