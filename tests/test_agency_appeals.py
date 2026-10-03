import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_organization_review import organization, review_data  # noqa: F401

from apps.core.models import AgencyAppeal, AgencyMember, AgencyReview, LegalAcceptance, User


@pytest.fixture
def rejected_agency(request):
    agency, original, reviewer = request.getfixturevalue("organization")
    data = {**review_data(), "outcome": "failed", "reason": "Falta contexto de organización"}
    assert reviewer.post(f"/es/moderation/organizations/{agency.pk}/", data).status_code == 302
    agency.refresh_from_db()
    owner = Client()
    owner.force_login(agency.owner)
    second = User.objects.create_user(
        username="agency-appeal-reviewer",
        email="agency-appeal@example.invalid",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    second.user_permissions.add(Permission.objects.get(codename="review_agency"))
    for acceptance in LegalAcceptance.objects.filter(user=original):
        LegalAcceptance.objects.create(
            user=second, document=acceptance.document, action=acceptance.action
        )
    independent = Client()
    independent.force_login(second)
    session = independent.session
    session["mfa_version"] = 1
    session.save()
    return agency, owner, reviewer, independent, AgencyReview.objects.get()


@pytest.mark.django_db(transaction=True)
def test_agency_appeal_reopens_without_verification_and_preserves_original(rejected_agency):
    agency, owner, original, independent, decision = rejected_agency
    path = f"/es/agency/decisions/{decision.pk}/appeal/"
    assert owner.post(path, {"explanation": "Solicito revisar documentación"}).status_code == 302
    assert owner.post(path, {"explanation": "Repetición"}).status_code == 302
    appeal = AgencyAppeal.objects.get()
    assert appeal.explanation == "Solicito revisar documentación"
    review_path = f"/es/moderation/agency-appeals/{appeal.pk}/"
    assert original.get(review_path).status_code == owner.get(review_path).status_code == 403
    assert (
        independent.post(
            review_path, {"result": "reconsider", "reason": "Reabrir para nueva comprobación"}
        ).status_code
        == 302
    )
    agency.refresh_from_db()
    assert agency.verification_status == "pending" and agency.review_version == 3
    assert not agency.verification_procedure
    assert AgencyReview.objects.get().outcome == "failed"
    assert (
        independent.post(review_path, {"result": "upheld", "reason": "Repetición"}).status_code
        == 409
    )
    assert b"Reabrir para nueva comprobaci" in owner.get(path).content
    assert (
        original.post(
            f"/es/moderation/organizations/{agency.pk}/", {**review_data(), "review_version": 2}
        ).status_code
        == 409
    )
    assert (
        independent.post(
            f"/es/moderation/organizations/{agency.pk}/", {**review_data(), "review_version": 3}
        ).status_code
        == 302
    )
    agency.refresh_from_db()
    assert agency.verification_status == "passed" and AgencyReview.objects.count() == 2
    assert owner.get(path).status_code == 200
    assert owner.post(path, {"explanation": "Reintento histórico"}).status_code == 302


@pytest.mark.django_db(transaction=True)
def test_agency_appeal_cannot_reopen_changed_state_or_be_resolved_by_member(rejected_agency):
    agency, owner, _, independent, decision = rejected_agency
    assert (
        owner.post(
            f"/es/agency/decisions/{decision.pk}/appeal/", {"explanation": "Solicito revisión"}
        ).status_code
        == 302
    )
    appeal = AgencyAppeal.objects.get()
    path = f"/es/moderation/agency-appeals/{appeal.pk}/"
    reviewer = User.objects.get(pk=independent.session["_auth_user_id"])
    membership = AgencyMember.objects.create(agency=agency, user=reviewer, active=False)
    assert (
        independent.post(path, {"result": "reconsider", "reason": "Conflicto"}).status_code == 403
    )
    membership.delete()
    agency.review_version += 1
    agency.save(update_fields=["review_version"])
    assert (
        independent.post(path, {"result": "reconsider", "reason": "Versión anterior"}).status_code
        == 400
    )
    appeal.refresh_from_db()
    assert appeal.status == "open"
