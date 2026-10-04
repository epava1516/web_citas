import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_drafts import contacts
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import Person, User
from apps.listings.lifecycle import act as lifecycle
from apps.listings.models import Listing, Revision
from apps.listings.moderation import decide, publicly_visible
from apps.safety.models import PrivacyPublicationHold
from apps.safety.privacy_holds import hold

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Private reviewed ground for precaution over public exposure"


def values(case, ground="accuracy"):
    return {"key": uuid.uuid4(), "version": case.version, "reason": REASON, "ground": ground}


def owner_client(person):
    actor = person.agency.owner
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    return actor, client


def pending_update(person):
    _, owner = owner_client(person)
    assert owner.post(f"/es/person/{person.pk}/listing/start/").status_code == 302
    revision = Revision.objects.filter(listing=person.listing, status="draft").latest("created_at")
    assert owner.post(f"/es/draft/{revision.pk}/2/", contacts(revision)).status_code == 302
    revision.refresh_from_db()
    assert (
        owner.post(
            f"/es/draft/{revision.pk}/submit/",
            {"edit_version": revision.edit_version, "declaration": True},
        ).status_code
        == 302
    )
    revision.refresh_from_db()
    assert revision.status == "pending"
    return revision


def test_hold_removes_exposure_and_blocks_forced_status_and_manager_lifecycle(
    request, settings, monkeypatch
):
    case, user, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "restriction"
    )
    listing = person.listing
    original = person.manager_version, person.phone_claim_id, person.subject_id
    Listing.objects.filter(pk=listing.pk).update(available_until=timezone.now())
    public = Client()
    detail = public.get(f"/en/listing/{listing.pk}/")
    assert detail.status_code == 200
    from django.urls import reverse

    photo = detail.context["photos"][0]
    image_url = reverse("public_photo", kwargs={"listing_id": listing.pk, "photo_id": photo.pk})
    payload = values(case)
    path = f"/en/moderation/rights/{case.pk}/publication-hold/"
    assert staff.post(path, payload).status_code == 302
    assert staff.post(path, payload).status_code == 302
    assert PrivacyPublicationHold.objects.count() == 1
    listing.refresh_from_db()
    person.refresh_from_db()
    assert listing.status == "paused" and listing.available_until is None
    assert (person.manager_version, person.phone_claim_id, person.subject_id) == original
    assert public.get(f"/en/listing/{listing.pk}/").status_code == 404
    assert public.get(image_url).status_code == 404
    Listing.objects.filter(pk=listing.pk).update(status="published")
    listing.refresh_from_db()
    assert not publicly_visible(listing)
    assert public.get("/en/", {"q": "photography"}).context["page"].paginator.count == 1
    assert public.get(f"/en/listing/{listing.pk}/").status_code == 404
    assert public.get(image_url).status_code == 404
    manager, _ = owner_client(person)
    for operation in ["resume", "renew", "available"]:
        with pytest.raises(ValidationError):
            lifecycle(manager, listing.pk, uuid.uuid4(), listing.lifecycle_version, operation, True)
    case.refresh_from_db()
    assert case.status == "reviewing" and case.scope_status == "unverified"
    assert REASON.encode() not in client.get(receipt).content
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    assert peer.phone_claim_id == original[1] and peer.manager_version == original[0]


@pytest.mark.parametrize("kind,ground", [("object", "objection_pending"), ("rectify", "accuracy")])
def test_ground_and_proof_scope_are_checked_and_case_stays_open(
    request, settings, monkeypatch, kind, ground
):
    case, user, _, _, _, _ = ready(request, settings, monkeypatch, kind)
    wrong = "accuracy" if kind == "object" else "claims"
    with pytest.raises(ValidationError):
        hold(user, case.pk, **values(case, wrong))
    proof = case.proofs.latest("created_at")
    proof.scope = "access"
    proof.save(update_fields=["scope"])
    with pytest.raises(ValidationError):
        hold(user, case.pk, **values(case, ground))
    proof.scope = kind
    proof.save(update_fields=["scope"])
    result = hold(user, case.pk, **values(case, ground))
    assert result.active and result.ground == ground
    case.refresh_from_db()
    assert case.status == "reviewing"
    with pytest.raises(ValidationError):
        hold(user, case.pk, **values(case, ground))


def test_approval_race_cannot_republish_held_profile(request, settings, monkeypatch):
    case, user, _, _, _, person = ready(request, settings, monkeypatch, "restriction")
    revision = pending_update(person)
    barrier = Barrier(2)

    def apply_hold():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return hold(actor, case.pk, **values(case)).pk
        finally:
            connections.close_all()

    def approve():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                decide(
                    actor,
                    revision.pk,
                    revision.edit_version,
                    "approved",
                    "Synthetic moderation decision during concurrent privacy review",
                )
                return "approved"
            except ValidationError:
                return "blocked"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        holding, approval = executor.submit(apply_hold), executor.submit(approve)
        assert holding.result(timeout=30)
        assert approval.result(timeout=30) in {"approved", "blocked"}
    listing = Listing.objects.get(pk=person.listing.pk)
    assert listing.status == "paused" and not publicly_visible(listing)
    assert PrivacyPublicationHold.objects.count() == 1
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404


def test_transfer_preserves_hold_and_guards_permissions_proof_and_csrf(
    request, settings, monkeypatch
):
    from django.contrib.auth.models import Permission
    from django.core.exceptions import PermissionDenied

    from apps.core.models import Agency
    from apps.listings.submissions import validate_submission

    case, user, staff, _, _, person = ready(request, settings, monkeypatch, "restriction")
    path = f"/en/moderation/rights/{case.pk}/publication-hold/"
    payload = values(case)
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    assert csrf.post(path, payload).status_code == 403
    stale = staff.session
    stale["mfa_version"] = user.mfa_version + 1
    stale.save()
    challenge = staff.post(path, payload)
    assert challenge.status_code == 302 and challenge.url == "/en/account/mfa/"
    assert not PrivacyPublicationHold.objects.exists()
    stale["mfa_version"] = user.mfa_version
    stale.save()
    permission = Permission.objects.get(codename="execute_rights_request")
    user.user_permissions.remove(permission)
    assert staff.post(path, payload).status_code == 403
    with pytest.raises(PermissionDenied):
        hold(User.objects.get(pk=user.pk), case.pk, **payload)
    user.user_permissions.add(permission)
    settings.PRODUCTION = True
    assert staff.post(path, payload).status_code == 409
    settings.PRODUCTION = False
    manager, owner = owner_client(person)
    assert owner.post(path, payload).status_code == 403
    result = hold(User.objects.get(pk=user.pk), case.pk, **payload)
    subject = person.subject
    subject_client = Client()
    subject_client.force_login(subject)
    target_owner = User.objects.create_user(
        username="synthetic-transfer-agency", email="transfer@example.invalid", role="agency"
    )
    target = Agency.objects.create(owner=target_owner, name="Synthetic transfer target")
    assert (
        subject_client.post(
            f"/es/person/{person.pk}/transfer/",
            {
                "target_agency": target.pk,
                "confirm": True,
                "manager_version": person.manager_version,
            },
        ).status_code
        == 302
    )
    person.refresh_from_db()
    result.refresh_from_db()
    assert person.agency_id == target.pk and result.active
    assert result.manager_version < person.manager_version
    with pytest.raises(ValidationError, match="Publication limited for privacy"):
        validate_submission(person.listing.approved_revision, person)
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404
    assert staff.get(path).status_code == 200
    assert b'name="reason"' not in staff.get(path).content


def test_mobile_hold_persists_after_reload_without_closing_request(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, person = ready(request, settings, monkeypatch, "restriction")
    listing_id = person.listing.pk
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
            page.locator("[name=purpose]").fill(
                "Review verified rights evidence before publication precaution"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            page.get_by_role("link", name="Apply privacy publication hold", exact=True).click()
            page.locator("[name=ground]").select_option("accuracy")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Apply reviewed measure", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            page.get_by_role("link", name="Apply privacy publication hold", exact=True).click()
            expect(page.get_by_text("Measure recorded", exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Measure recorded", exact=False)).to_be_visible()
            assert page.locator("[name=reason]").count() == 0
            public = browser.new_page()
            response = public.goto(live_server.url + f"/en/listing/{listing_id}/")
            assert response.status == 404
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing" and PrivacyPublicationHold.objects.count() == 1
