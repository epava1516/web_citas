from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import scenario  # noqa: F401

from apps.core.models import Agency, AgencyMember, AgencyReview, LegalAcceptance, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def organization(request):
    owner, _, _ = request.getfixturevalue("scenario")
    agency = Agency.objects.create(owner=owner, name="Agencia sintética")
    moderator = User.objects.create_user(
        username="org-moderator",
        email="moderator@example.invalid",
        password="Long-moderator-password!847",
        email_verified_at=timezone.now(),
        mfa_enabled=True,
        mfa_version=1,
    )
    moderator.user_permissions.add(Permission.objects.get(codename="review_agency"))
    for acceptance in LegalAcceptance.objects.filter(user=owner):
        LegalAcceptance.objects.create(
            user=moderator, document=acceptance.document, action=acceptance.action
        )
    client = Client()
    client.force_login(moderator)
    session = client.session
    session["mfa_version"] = 1
    session.save()
    return agency, moderator, client


def review_data():
    return {
        "review_version": 1,
        "outcome": "passed",
        "reason": "Comprobación sintética de pruebas",
        "evidence_reference": "synthetic-reference-1",
    }


def test_organization_decision_persists_and_replay_conflicts(organization):
    agency, moderator, client = organization
    path = f"/es/moderation/organizations/{agency.pk}/"
    assert agency.name.encode() in client.get("/es/moderation/organizations/").content
    assert client.post(path, review_data()).status_code == 302
    agency.refresh_from_db()
    assert (
        agency.verification_status == "passed" and agency.verification_procedure == "simulator-v1"
    )
    review = AgencyReview.objects.get()
    assert review.reviewer_id == moderator.pk
    assert review.evidence_reference == "synthetic-reference-1"
    page = client.get(path)
    assert b"Comprobaci" in page.content and page["Cache-Control"] == "private, no-store"
    assert client.post(path, review_data()).status_code == 409
    assert AgencyReview.objects.count() == 1


def test_permissions_mfa_self_review_and_csrf(organization):
    agency, moderator, client = organization
    path = f"/es/moderation/organizations/{agency.pk}/"
    assert Client().get(path).status_code == 302
    moderator.user_permissions.clear()
    assert client.get(path).status_code == 403
    moderator.user_permissions.add(Permission.objects.get(codename="review_agency"))
    session = client.session
    session.pop("mfa_version")
    session.save()
    assert client.get(path).status_code == 302  # Account gate requires MFA even without is_staff.
    session = client.session
    session["mfa_version"] = 1
    session.save()
    AgencyMember.objects.create(agency=agency, user=moderator)
    assert client.post(path, review_data()).status_code == 403
    AgencyMember.objects.all().delete()
    own = Agency.objects.create(owner=moderator, name="Moderator own agency")
    assert client.post(f"/es/moderation/organizations/{own.pk}/", review_data()).status_code == 403
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(moderator)
    session = strict.session
    session["mfa_version"] = 1
    session.save()
    assert strict.post(path, review_data()).status_code == 403
    assert not AgencyReview.objects.exists()


def test_invalid_input_and_production_simulation_blocked(organization, settings):
    agency, _, client = organization
    path = f"/es/moderation/organizations/{agency.pk}/"
    assert client.post(path, {**review_data(), "reason": ""}).status_code == 400
    assert client.post(path, {**review_data(), "outcome": "unknown"}).status_code == 400
    settings.PRODUCTION = True
    assert client.post(path, review_data()).status_code == 503
    agency.refresh_from_db()
    assert agency.verification_status == "pending" and not AgencyReview.objects.exists()


def test_concurrent_decisions_keep_one_record(organization):
    agency, moderator, _ = organization
    barrier = Barrier(2)

    def decide():
        close_old_connections()
        try:
            local = Client()
            local.force_login(moderator)
            session = local.session
            session["mfa_version"] = 1
            session.save()
            barrier.wait(timeout=5)
            return local.post(
                f"/es/moderation/organizations/{agency.pk}/", review_data()
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: decide(), range(2))) == [302, 409]
    assert AgencyReview.objects.count() == 1
