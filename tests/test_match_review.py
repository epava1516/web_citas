from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import contacts, details, scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import payload, prepared  # noqa: F401

from apps.core.models import LegalAcceptance, Person, PhoneClaim, User
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Match, MatchResolution

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def conflict(request):
    original_person, owner, original, moderator, reviewer = request.getfixturevalue("published")
    user = User.objects.create_user(
        username="second-subject",
        email="second-subject@example.invalid",
        password="Long-second-password!847",
        email_verified_at=timezone.now(),
    )
    for acceptance in LegalAcceptance.objects.filter(
        user=original_person.individual, action__in=["account_terms", "privacy_notice"]
    ):
        LegalAcceptance.objects.create(
            user=user, document=acceptance.document, action=acceptance.action
        )
    phone = PhoneClaim.objects.create(
        individual=user, phone="+34600777111", verified_at=timezone.now()
    )
    person = Person.objects.create(
        individual=user, subject=user, alias="Segunda persona sintética", phone_claim=phone
    )
    client = Client()
    client.force_login(user)
    assert (
        client.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 302
    )
    assert client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 302
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get(listing__person=person)
    assert client.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 302
    revision.refresh_from_db()
    assert client.post(f"/es/draft/{revision.pk}/2/", contacts(revision)).status_code == 302
    assert upload(client, revision, raw_image()).status_code == 302
    revision.refresh_from_db()
    assert client.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 302
    match = Match.objects.filter(photo__revision=revision, candidate__revision=original).get()
    return original, revision, match, moderator, reviewer, owner, client


def resolution(match, **changes):
    return {
        "review_version": match.review_version,
        "outcome": "distinct_people",
        "reason": "Autorizaciones de ambas personas revisadas",
        "evidence_reference": "synthetic-authorizations",
        **changes,
    }


def test_distinct_authorized_people_resolves_both_directions_without_suspension(conflict):
    original, revision, match, _, reviewer, _, _ = conflict
    path = f"/es/moderation/matches/{match.pk}/"
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 400
    )
    response = reviewer.get(path + "candidate/image/")
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    response.close()
    assert reviewer.post(path, resolution(match)).status_code == 302
    assert not Match.objects.filter(resolved_at__isnull=True).exists()
    assert MatchResolution.objects.count() == 2
    assert reviewer.post(path, resolution(match)).status_code == 400
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 302
    )
    assert all(User.objects.values_list("is_active", flat=True))
    assert Client().get(f"/es/listing/{original.listing_id}/").status_code == 200


def test_confirmed_conflict_pauses_publication_and_remains_blocking(conflict):
    original, revision, match, _, reviewer, _, _ = conflict
    path = f"/es/moderation/matches/{match.pk}/"
    assert reviewer.post(path, resolution(match, outcome="conflict")).status_code == 302
    listing = Listing.objects.get(pk=original.listing_id)
    assert listing.status == "paused"
    assert Client().get(f"/es/listing/{listing.pk}/").status_code == 404
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 400
    )
    match.refresh_from_db()
    assert reviewer.post(path, resolution(match)).status_code == 302
    listing.refresh_from_db()
    assert listing.status == "paused"  # Clearing evidence never auto-republishes.


def test_exact_not_false_positive_and_permissions_cover_both_people(conflict):
    _, _, match, moderator, reviewer, owner, other = conflict
    path = f"/es/moderation/matches/{match.pk}/"
    assert reviewer.post(path, resolution(match, outcome="false_positive")).status_code == 400
    assert owner.get(path).status_code == other.get(path).status_code == 403
    assert Client().get(path + "photo/image/").status_code == 302
    person = match.candidate.revision.listing.person
    original_subject = person.subject
    person.subject = moderator
    person.save(update_fields=["subject"])
    assert reviewer.post(path, resolution(match)).status_code == 403
    person.subject = original_subject
    person.save(update_fields=["subject"])
    moderator.user_permissions.clear()
    assert reviewer.get(path).status_code == 403
    assert not MatchResolution.objects.exists()


def test_approximate_false_positive_can_be_resolved(conflict):
    original, revision, _, _, reviewer, _, other = conflict
    # Create a correction through the real revision flow; pending content stays frozen.
    response = other.post(f"/es/person/{revision.listing.person_id}/listing/start/")
    assert response.status_code == 302
    revision = Revision.objects.get(pk=response.url.split("/")[3])
    old = revision.photos.get()
    assert other.post(f"/es/photos/{old.pk}/remove/").status_code == 302
    assert upload(other, revision, raw_image(seed=93)).status_code == 302
    photo = revision.photos.get(removed_at__isnull=True)
    candidate = original.photos.get()
    match, _ = Match.objects.get_or_create(
        photo=photo, candidate=candidate, defaults={"method": "regional", "score": 0.85}
    )
    assert (
        reviewer.post(
            f"/es/moderation/matches/{match.pk}/", resolution(match, outcome="false_positive")
        ).status_code
        == 302
    )
    match.refresh_from_db()
    assert match.decision == "false_positive"


def test_concurrent_resolutions_have_one_winner(conflict):
    _, _, match, moderator, _, _, _ = conflict
    barrier = Barrier(2)

    def resolve():
        close_old_connections()
        try:
            local = Client()
            local.force_login(moderator)
            session = local.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return local.post(f"/es/moderation/matches/{match.pk}/", resolution(match)).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: resolve(), range(2))) == [302, 400]
    assert MatchResolution.objects.count() == 2
