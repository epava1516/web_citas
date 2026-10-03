from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import LegalAcceptance, User
from apps.listings.models import Appeal, ModerationDecision, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def rejected(request):
    person, owner, revision, moderator, reviewer = request.getfixturevalue("pending")
    assert (
        reviewer.post(
            f"/es/moderation/listings/{revision.pk}/",
            decision(revision, outcome="rejected", reason="Revisar descripción"),
        ).status_code
        == 302
    )
    review_user = User.objects.create_user(
        username="appeal-reviewer",
        email="appeal-reviewer@example.invalid",
        password="Long-appeal-password!847",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    review_user.user_permissions.set(moderator.user_permissions.all())
    for acceptance in LegalAcceptance.objects.filter(user=moderator):
        LegalAcceptance.objects.create(
            user=review_user, document=acceptance.document, action=acceptance.action
        )
    independent = Client()
    independent.force_login(review_user)
    session = independent.session
    session["mfa_version"] = 1
    session.save()
    return person, owner, revision, reviewer, review_user, independent


def test_appeal_private_idempotent_and_independent_review(rejected):
    _, owner, revision, original_reviewer, _, independent = rejected
    moderation_decision = revision.decisions.get()
    path = f"/es/draft/decisions/{moderation_decision.pk}/appeal/"
    assert (
        owner.post(path, {"explanation": "Solicito reconsiderar los datos sintéticos"}).status_code
        == 302
    )
    assert owner.post(path, {"explanation": "Retry"}).status_code == 302
    appeal = Appeal.objects.get()
    assert appeal.explanation != "Retry"
    photo = revision.photos.get()
    image = independent.get(f"/es/moderation/photos/{photo.pk}/")
    assert image.status_code == 200 and image["Cache-Control"] == "private, no-store"
    image.close()
    assert owner.get(path)["Cache-Control"] == "private, no-store"
    assert Client().get(path).status_code == 302
    review_path = f"/es/moderation/appeals/{appeal.pk}/"
    assert original_reviewer.get(review_path).status_code == 403
    assert owner.get(review_path).status_code == 403
    assert (
        independent.post(
            review_path, {"result": "reconsider", "reason": "Procede nueva revisión humana"}
        ).status_code
        == 302
    )
    appeal.refresh_from_db()
    revision.refresh_from_db()
    assert appeal.status == "resolved" and appeal.resolved_at
    assert revision.status == "pending" and not revision.listing.approved_revision_id
    assert b"Procede nueva" in owner.get(path).content
    assert (
        independent.post(review_path, {"result": "upheld", "reason": "Repeat"}).status_code == 409
    )


def test_invalid_appeal_and_obsolete_manager_cannot_reopen(rejected):
    person, owner, revision, _, _, independent = rejected
    path = f"/es/draft/decisions/{revision.decisions.get().pk}/appeal/"
    assert owner.post(path, {"explanation": ""}).status_code == 400
    assert not Appeal.objects.exists()
    assert owner.post(path, {"explanation": "Contenido sintético para revisar"}).status_code == 302
    appeal = Appeal.objects.get()
    person.manager_version += 1
    person.save(update_fields=["manager_version"])
    review_path = f"/es/moderation/appeals/{appeal.pk}/"
    assert (
        independent.post(
            review_path, {"result": "reconsider", "reason": "Nueva evaluación"}
        ).status_code
        == 400
    )
    appeal.refresh_from_db()
    assert appeal.status == "open"
    assert (
        independent.post(
            review_path, {"result": "upheld", "reason": "Se necesita borrador con gestor vigente"}
        ).status_code
        == 302
    )
    assert owner.post(path, {"explanation": "Late repeat"}).status_code == 404


def test_concurrent_appeal_resolutions_keep_one_result(rejected):
    _, owner, revision, _, review_user, _ = rejected
    owner.post(
        f"/es/draft/decisions/{revision.decisions.get().pk}/appeal/",
        {"explanation": "Revisión sintética"},
    )
    appeal = Appeal.objects.get()
    barrier = Barrier(2)

    def resolve():
        close_old_connections()
        try:
            client = Client()
            client.force_login(review_user)
            session = client.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return client.post(
                f"/es/moderation/appeals/{appeal.pk}/",
                {"result": "upheld", "reason": "Decisión sintética mantenida"},
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: resolve(), range(2))) == [302, 409]
    appeal.refresh_from_db()
    assert appeal.status == "resolved"


@pytest.mark.parametrize("state", ["quota", "newer_decision"])
def test_reconsideration_respects_current_rejection_and_pending_quota(rejected, state):
    _, owner, revision, _, review_user, independent = rejected
    owner.post(
        f"/es/draft/decisions/{revision.decisions.get().pk}/appeal/",
        {"explanation": "Revisión sintética"},
    )
    appeal = Appeal.objects.get()
    if state == "quota":
        for _ in range(3):
            Revision.objects.create(
                listing=revision.listing, manager_version=revision.manager_version
            )
    else:
        ModerationDecision.objects.create(
            revision=revision,
            reviewer=review_user,
            outcome="rejected",
            reason="Decisión posterior sintética",
        )
    assert (
        independent.post(
            f"/es/moderation/appeals/{appeal.pk}/", {"result": "reconsider", "reason": "Reabrir"}
        ).status_code
        == 400
    )
    appeal.refresh_from_db()
    revision.refresh_from_db()
    assert appeal.status == "open" and revision.status == "rejected"
