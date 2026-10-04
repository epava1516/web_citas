import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_verification import prepared, read

from apps.core.models import Person, User
from apps.listings.lifecycle import act as lifecycle
from apps.listings.models import Listing, Revision
from apps.safety.models import RightsAction, RightsWithdrawal
from apps.safety.rights_actions import act
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def approved(request, settings):
    case, user, staff, person, verifier, other = prepared(request, settings)
    proof = start(
        user, case.pk, uuid.uuid4(), case.version, "Synthetic proportional rights procedure"
    )
    case.refresh_from_db()
    read(other, case)
    receive_event(
        verifier,
        simulate_event(
            proof.pk, uuid.uuid4(), case.version, "passed", "Independent synthetic scope assessment"
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    user.user_permissions.add(Permission.objects.get(codename="execute_rights_request"))
    return case, User.objects.get(pk=user.pk), staff, person


def test_no_account_withdrawal_hides_only_scoped_profile_and_revokes_representation(
    request, settings
):
    case, _, staff, person = approved(request, settings)
    assert case.actor_id is None
    public = Client()
    listing = person.listing
    detail = f"/en/listing/{listing.pk}/"
    response = public.get(detail)
    assert response.status_code == 200
    photo = response.context["photos"][0]
    from django.urls import reverse

    photo_path = reverse("public_photo", kwargs={"listing_id": listing.pk, "photo_id": photo.pk})
    assert public.get(photo_path).status_code == 200
    manager_version, lifecycle_version = person.manager_version, listing.lifecycle_version
    other_person = Person.objects.get(individual__username="fixture-v1-individual")
    other_state = other_person.manager_version, other_person.listing.lifecycle_version
    same_agency = Person.objects.get(subject__username="fixture-v1-model-b")
    assert same_agency.agency_id == person.agency_id
    agency_peer_state = (
        same_agency.manager_version,
        same_agency.phone_claim_id,
        same_agency.subject_id,
        same_agency.listing.status,
    )
    original = case.received_at, case.initial_due_at
    pending = Revision.objects.create(
        listing=listing, manager_version=person.manager_version, status="pending"
    )
    Listing.objects.filter(pk=listing.pk).update(available_until=timezone.now())
    path, submitted = action(staff, case, "withdraw")
    assert staff.post(path, submitted).status_code == 302
    assert staff.post(path, submitted).status_code == 302
    case.refresh_from_db()
    person.refresh_from_db()
    listing.refresh_from_db()
    pending.refresh_from_db()
    assert person.manager_version == manager_version + 1
    assert person.consent_revoked_at and person.consent_version == 0
    assert person.age_status == "pending" and person.manager_review_status == "pending"
    assert person.assigned_editor_id is None and person.phone_claim_id is None
    assert listing.status == pending.status == "withdrawn"
    assert listing.lifecycle_version == lifecycle_version + 1 and listing.available_until is None
    assert case.status == "withdrawn" and case.version == 6
    assert (case.received_at, case.initial_due_at) == original
    assert RightsWithdrawal.objects.count() == 1
    assert public.get(detail).status_code == public.get(photo_path).status_code == 404
    assert listing.pk not in [item.pk for item in public.get("/en/").context["page"]]
    # The same agency still owns the profile, but has no current authorization to publish it.
    assert person.agency_id and person.subject_id
    other_person.refresh_from_db()
    assert (other_person.manager_version, other_person.listing.lifecycle_version) == other_state
    assert public.get(f"/en/listing/{other_person.listing.pk}/").status_code == 200
    same_agency.refresh_from_db()
    assert (
        same_agency.manager_version,
        same_agency.phone_claim_id,
        same_agency.subject_id,
        same_agency.listing.status,
    ) == agency_peer_state
    owner = person.agency.owner
    with pytest.raises(ValidationError):
        lifecycle(owner, listing.pk, uuid.uuid4(), lifecycle_version, "available")
    with pytest.raises(ValidationError):
        lifecycle(owner, listing.pk, uuid.uuid4(), listing.lifecycle_version, "resume")
    Listing.objects.filter(pk=listing.pk).update(status="published")
    assert public.get(detail).status_code == public.get(photo_path).status_code == 404


def test_execution_permission_current_read_and_proof_required(request, settings):
    case, user, staff, person = approved(request, settings)
    path, submitted = action(staff, case, "withdraw")
    user.user_permissions.remove(Permission.objects.get(codename="execute_rights_request"))
    assert staff.post(path, submitted).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="execute_rights_request"))
    case.accesses.filter(actor=user, case_version=case.version).delete()
    assert staff.post(path, submitted).status_code == 409
    read(staff, case)
    settings.PRODUCTION = True
    assert staff.post(path, submitted).status_code == 409
    settings.PRODUCTION = False
    case.proofs.update(expires_at=timezone.now())
    assert staff.post(path, submitted).status_code == 409
    assert not RightsWithdrawal.objects.exists()
    person.refresh_from_db()
    assert person.manager_version == case.manager_version


def test_failed_storage_rolls_back_case_and_person(request, settings, monkeypatch):
    case, user, _, person = approved(request, settings)
    version = person.manager_version

    def fail(*args, **kwargs):
        raise RuntimeError("Synthetic persistence failure")

    monkeypatch.setattr(RightsWithdrawal.objects, "create", fail)
    with pytest.raises(RuntimeError):
        act(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "withdraw",
            "Execute scoped synthetic withdrawal",
        )
    case.refresh_from_db()
    person.refresh_from_db()
    assert case.version == 5 and case.status == "reviewing"
    assert person.manager_version == version and person.listing.status == "published"
    assert not RightsAction.objects.filter(operation="withdraw").exists()


def test_concurrent_exact_withdrawal_only_mutates_once(request, settings):
    case, user, _, person = approved(request, settings)
    key = uuid.uuid4()
    previous_version = person.manager_version
    barrier = Barrier(2)

    def withdraw(_):
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return act(
                actor, case.pk, key, case.version, "withdraw", "Execute scoped synthetic withdrawal"
            ).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(withdraw, range(2)))
    assert outcomes == [case.pk, case.pk]
    person.refresh_from_db()
    assert person.manager_version == previous_version + 1
    assert RightsWithdrawal.objects.count() == 1


def test_mobile_reviewer_withdraws_scoped_anonymous_representation(
    live_server, request, settings, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, person = approved(request, settings)
    assert case.actor_id is None
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/")
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("withdraw")
            page.locator("[name=reason]").fill(
                "Execute anonymous synthetic representation withdrawal"
            )
            page.get_by_role("button", name="Record assignment action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            page.reload()
            assert "withdrawn" in page.content()
            assert "rights-private@example.invalid" not in page.content()
            public = browser.new_page(viewport={"width": 390, "height": 844})
            assert public.goto(live_server.url + f"/en/listing/{person.listing.pk}/").status == 404
        finally:
            browser.close()
    assert RightsWithdrawal.objects.count() == 1
