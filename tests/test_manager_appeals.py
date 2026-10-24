import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import LegalAcceptance, LegalDocument, ManagerAppeal, ManagerReview, User


@pytest.fixture
def manager_rejection(request):
    person, owner, revision, moderator, reviewer = request.getfixturevalue("pending")
    phone = person.phone_claim
    assert (
        owner.post(
            f"/es/person/{person.pk}/transfer/", {"manager_version": 1, "confirm": "on"}
        ).status_code
        == 302
    )
    person.refresh_from_db()
    assert (
        owner.post(
            f"/es/person/{person.pk}/consent/",
            {
                "authorize": "on",
                "version": LegalDocument.objects.get(
                    slug="publishing", language="es", active=True
                ).version,
            },
        ).status_code
        == 302
    )
    assert owner.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 302
    person.refresh_from_db()
    person.phone_claim = phone
    person.save(update_fields=["phone_claim"])
    assert (
        reviewer.post(
            f"/es/moderation/managers/{person.pk}/",
            {
                "manager_version": person.manager_version,
                "outcome": "failed",
                "reason": "Comprobación adicional requerida",
            },
        ).status_code
        == 302
    )
    second = User.objects.create_user(
        username="independent-manager-review",
        email="independent@example.invalid",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    second.user_permissions.add(Permission.objects.get(codename="review_listing"))
    for acceptance in LegalAcceptance.objects.filter(user=moderator):
        LegalAcceptance.objects.create(
            user=second, document=acceptance.document, action=acceptance.action
        )
    independent = Client()
    independent.force_login(second)
    session = independent.session
    session["mfa_version"] = 1
    session.save()
    decision = ManagerReview.objects.get()
    return person, owner, revision, reviewer, independent, decision


@pytest.mark.django_db(transaction=True)
def test_manager_appeal_independence_persistence_and_no_auto_publication(manager_rejection):
    person, owner, revision, original, independent, decision = manager_rejection
    path = f"/es/person/manager-decisions/{decision.pk}/appeal/"
    assert (
        owner.post(path, {"explanation": "Aporto contexto para revisar la decisión"}).status_code
        == 302
    )
    assert owner.post(path, {"explanation": "Reintento no reemplaza texto"}).status_code == 302
    appeal = ManagerAppeal.objects.get()
    assert appeal.explanation == "Aporto contexto para revisar la decisión"
    review_path = f"/es/moderation/manager-appeals/{appeal.pk}/"
    assert original.get(review_path).status_code == owner.get(review_path).status_code == 403
    assert (
        independent.post(
            review_path, {"result": "approved", "reason": "Revisadas las autorizaciones actuales"}
        ).status_code
        == 302
    )
    person.refresh_from_db()
    appeal.refresh_from_db()
    assert person.manager_review_status == "approved" and appeal.status == "resolved"
    assert ManagerReview.objects.get().outcome == "failed"
    assert (
        independent.post(review_path, {"result": "upheld", "reason": "Repetición"}).status_code
        == 409
    )
    assert Client().get(f"/es/listing/{revision.listing_id}/").status_code == 404
    assert b"Revisadas las autorizaciones actuales" in owner.get(path).content


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("changed", ["version", "consent"])
def test_manager_appeal_cannot_approve_obsolete_authorization(manager_rejection, changed):
    person, owner, _, _, independent, decision = manager_rejection
    path = f"/es/person/manager-decisions/{decision.pk}/appeal/"
    assert owner.post(path, {"explanation": "Solicito revisión"}).status_code == 302
    appeal = ManagerAppeal.objects.get()
    if changed == "version":
        person.manager_version += 1
    else:
        person.consent_revoked_at = timezone.now()
    person.save()
    assert (
        independent.post(
            f"/es/moderation/manager-appeals/{appeal.pk}/",
            {"result": "approved", "reason": "No debe aprobar"},
        ).status_code
        == 400
    )
    appeal.refresh_from_db()
    assert appeal.status == "open"
    if changed == "version":
        assert owner.get(path).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_manager_appeal_resolution_records_one_result(manager_rejection):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    _, owner, _, _, independent, decision = manager_rejection
    assert (
        owner.post(
            f"/es/person/manager-decisions/{decision.pk}/appeal/",
            {"explanation": "Revisión concurrente"},
        ).status_code
        == 302
    )
    appeal = ManagerAppeal.objects.get()
    moderator = User.objects.get(pk=independent.session["_auth_user_id"])
    barrier = Barrier(2)

    def resolve(result):
        close_old_connections()
        try:
            client = Client()
            client.force_login(moderator)
            session = client.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return client.post(
                f"/es/moderation/manager-appeals/{appeal.pk}/",
                {"result": result, "reason": f"Resolución {result}"},
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(resolve, ["approved", "upheld"])) == [302, 409]
    appeal.refresh_from_db()
    assert appeal.status == "resolved" and appeal.reason == f"Resolución {appeal.result}"
