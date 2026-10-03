import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_match_review import conflict, resolution  # noqa: F401
from test_photo_restrictions import restricted  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import LegalAcceptance, User
from apps.mediafiles.models import Match, MatchResolution, PhotoAppeal


def independent_reviewer(original_moderator):
    moderator = User.objects.create_user(
        username="photo-independent",
        email="photo-independent@example.invalid",
        password="Long-moderator-password!847",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    moderator.user_permissions.add(Permission.objects.get(codename="review_listing"))
    for acceptance in LegalAcceptance.objects.filter(
        user=original_moderator, action__in=["account_terms", "privacy_notice"]
    ):
        LegalAcceptance.objects.create(
            user=moderator, document=acceptance.document, action=acceptance.action
        )
    independent = Client()
    independent.force_login(moderator)
    session = independent.session
    session["mfa_version"] = 1
    session.save()
    return moderator, independent


@pytest.fixture
def photo_case(request):
    values, notices = request.getfixturevalue("restricted")
    original, _, _, original_moderator, _, owner, _ = values
    assert (
        owner.post(
            f"/es/person/photo-restrictions/{notices[0].pk}/",
            {"explanation": "Tengo autorización para mi fotografía"},
        ).status_code
        == 302
    )
    moderator, independent = independent_reviewer(original_moderator)
    return values, notices, PhotoAppeal.objects.get(), moderator, independent


@pytest.mark.django_db(transaction=True)
def test_photo_appeal_reopens_pair_without_publication_or_counterpart_data(photo_case):
    values, notices, appeal, _, independent = photo_case
    original, revision, _, _, original_reviewer, owner, other = values
    path = f"/es/moderation/photo-appeals/{appeal.pk}/"
    assert (
        original_reviewer.get(path).status_code
        == owner.get(path).status_code
        == other.get(path).status_code
        == 403
    )
    assert (
        owner.post(
            f"/es/person/photo-restrictions/{notices[0].pk}/", {"explanation": "Repetición"}
        ).status_code
        == 302
    )
    appeal.refresh_from_db()
    assert appeal.explanation == "Tengo autorización para mi fotografía"
    assert (
        independent.post(
            path, {"result": "reconsider", "reason": "Se revisarán las autorizaciones de uso"}
        ).status_code
        == 302
    )
    assert Match.objects.filter(resolved_at__isnull=True, decision="").count() == 2
    assert MatchResolution.objects.filter(outcome="conflict").count() == 2
    assert MatchResolution.objects.filter(outcome="reopened").count() == 2
    assert independent.post(path, {"result": "upheld", "reason": "Repetición"}).status_code == 409
    assert Client().get(f"/es/listing/{original.listing_id}/").status_code == 404
    assert (
        independent.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 400
    )
    response = owner.get(f"/es/person/photo-restrictions/{notices[0].pk}/")
    assert "Pendiente de nueva revisión humana" in response.content.decode()
    assert str(notices[1].photo_id).encode() not in response.content
    assert b"second-subject@example.invalid" not in response.content


@pytest.mark.django_db(transaction=True)
def test_photo_appeal_cannot_reopen_superseded_decision(photo_case):
    values, _, appeal, _, independent = photo_case
    _, _, match, _, reviewer, _, _ = values
    match.refresh_from_db()
    assert (
        reviewer.post(
            f"/es/moderation/matches/{match.pk}/", resolution(match, outcome="conflict")
        ).status_code
        == 302
    )
    assert (
        independent.post(
            f"/es/moderation/photo-appeals/{appeal.pk}/",
            {"result": "reconsider", "reason": "No reemplazar decisión más reciente"},
        ).status_code
        == 400
    )
    appeal.refresh_from_db()
    assert appeal.status == "open" and not Match.objects.filter(resolved_at__isnull=True).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_photo_appeal_resolution_reopens_once(photo_case):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    _, _, appeal, moderator, _ = photo_case
    barrier = Barrier(2)

    def resolve():
        close_old_connections()
        try:
            client = Client()
            client.force_login(moderator)
            session = client.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return client.post(
                f"/es/moderation/photo-appeals/{appeal.pk}/",
                {"result": "reconsider", "reason": "Nueva revisión humana"},
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: resolve(), range(2))) == [302, 409]
    assert MatchResolution.objects.filter(outcome="reopened").count() == 2
    assert set(Match.objects.values_list("review_version", flat=True)) == {3}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("person_index", [0, 1])
def test_qualified_moderator_with_own_person_cannot_resolve_photo_appeal(photo_case, person_index):
    values, notices, appeal, _, _ = photo_case
    client = values[5 + person_index]
    person = notices[person_index].person
    user = person.subject
    user.mfa_enabled = True
    user.mfa_version = 1
    user.save(update_fields=["mfa_enabled", "mfa_version"])
    user.user_permissions.add(Permission.objects.get(codename="review_listing"))
    client.force_login(user)
    session = client.session
    session["mfa_version"] = 1
    session.save()
    assert (
        client.post(
            f"/es/moderation/photo-appeals/{appeal.pk}/",
            {"result": "reconsider", "reason": "Conflicto de interés"},
        ).status_code
        == 403
    )
    appeal.refresh_from_db()
    assert appeal.status == "open"
