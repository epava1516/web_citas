import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import PrivacyHoldReleaseProposal
from apps.safety.privacy_holds import hold
from apps.safety.privacy_release import execute, propose
from apps.safety.rights_actions import act
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Reviewed private ground for ending this publication precaution"


def fresh(case, user, staff, verifier, other):
    case.refresh_from_db()
    read(staff, case)
    proof = start(
        user, case.pk, uuid.uuid4(), case.version, "Fresh synthetic independent rights procedure"
    )
    case.refresh_from_db()
    read(other, case)
    receive_event(
        verifier,
        simulate_event(
            proof.pk,
            uuid.uuid4(),
            case.version,
            "passed",
            "Independent synthetic assessment after reviewed notification",
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    return proof


def prepared(request, settings, monkeypatch, kind="restriction"):
    case, original, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "restriction"
    )
    held = hold(
        original,
        case.pk,
        uuid.uuid4(),
        case.version,
        REASON,
        "objection_pending" if kind == "object" else "accuracy",
    )
    original.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["manage_rights_assignment", "verify_rights_scope", "review_privacy_hold"]
        )
    )
    original = User.objects.get(pk=original.pk)
    case.refresh_from_db()
    act(original, case.pk, uuid.uuid4(), case.version, "unassign", REASON)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["execute_rights_request", "respond_rights_request", "review_privacy_hold"]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    case.refresh_from_db()
    act(reviewer, case.pk, uuid.uuid4(), case.version, "claim", REASON)
    fresh(case, reviewer, other, original, staff)
    return case, reviewer, other, original, staff, client, receipt, person, held


def plan(case, user):
    values = {"key": uuid.uuid4(), "version": case.version, "reason": REASON}
    proposal = propose(user, case.pk, **values)
    assert propose(user, case.pk, **values).pk == proposal.pk
    case.refresh_from_db()
    return proposal


def confirm(client, receipt, proposal):
    assert (
        client.post(
            receipt + f"response/{proposal.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )


@pytest.mark.parametrize("kind", ["restriction", "object", "rectify"])
def test_independent_notified_release_keeps_request_open_and_listing_paused(
    request, settings, monkeypatch, kind
):
    case, user, staff, verifier, other, client, receipt, person, held = prepared(
        request, settings, monkeypatch, kind
    )
    dates = (case.received_at, case.initial_due_at)
    proposal = plan(case, user)
    assert held.active
    assert b"Release of the publication hold is proposed" in client.get(receipt).content
    assert REASON.encode() not in client.get(receipt).content
    with pytest.raises(ValidationError):
        execute(user, case.pk, uuid.uuid4(), case.version, proposal.pk, REASON)
    confirm(client, receipt, proposal)
    newproof = fresh(case, user, staff, verifier, other)
    data = {
        "key": uuid.uuid4(),
        "version": case.version,
        "proposal_id": proposal.pk,
        "reason": REASON,
    }
    path = f"/en/moderation/rights/{case.pk}/publication-hold/release/"
    assert staff.post(path, data | {"operation": "execute"}).status_code == 302
    assert staff.post(path, data | {"operation": "execute"}).status_code == 302
    proposal.refresh_from_db()
    held.refresh_from_db()
    case.refresh_from_db()
    assert not held.active and proposal.released_at and proposal.released_proof_id == newproof.pk
    assert case.status == "reviewing" and case.scope_status == "unverified"
    assert (case.received_at, case.initial_due_at) == dates
    listing = person.listing
    listing.refresh_from_db()
    assert listing.status == "paused" and listing.available_until is None
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404
    assert b"Release recorded" in staff.get(path).content
    assert b"private@example.invalid" not in staff.get(path).content


def test_original_actor_and_stale_source_or_simulated_production_cannot_release(
    request, settings, monkeypatch
):
    case, user, staff, original, _, client, receipt, person, held = prepared(
        request, settings, monkeypatch
    )
    with pytest.raises(PermissionDenied):
        propose(original, case.pk, uuid.uuid4(), case.version, REASON)
    proposal = plan(case, user)
    confirm(client, receipt, proposal)
    verifier = User.objects.get(pk=original.pk)
    other = Client()
    other.force_login(verifier)
    session = other.session
    session["mfa_version"] = verifier.mfa_version
    session.save()
    fresh(case, user, staff, verifier, other)
    settings.PRODUCTION = True
    with pytest.raises(ValidationError):
        execute(user, case.pk, uuid.uuid4(), case.version, proposal.pk, REASON)
    settings.PRODUCTION = False
    listing = person.listing
    listing.refresh_from_db()
    listing.lifecycle_version += 1
    listing.save(update_fields=["lifecycle_version"])
    with pytest.raises(ValidationError):
        execute(user, case.pk, uuid.uuid4(), case.version, proposal.pk, REASON)
    held.refresh_from_db()
    assert held.active
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    assert (
        csrf.post(
            f"/en/moderation/rights/{case.pk}/publication-hold/release/", {"operation": "execute"}
        ).status_code
        == 403
    )


def test_fresh_check_started_before_acknowledgement_is_insufficient(request, settings, monkeypatch):
    case, user, staff, verifier, other, client, receipt, _, held = prepared(
        request, settings, monkeypatch
    )
    proposal = plan(case, user)
    fresh(case, user, staff, verifier, other)
    with pytest.raises(ValidationError):
        execute(user, case.pk, uuid.uuid4(), case.version, proposal.pk, REASON)
    confirm(client, receipt, proposal)
    with pytest.raises(ValidationError):
        execute(user, case.pk, uuid.uuid4(), case.version, proposal.pk, REASON)
    held.refresh_from_db()
    assert held.active


def test_concurrent_release_replay_executes_one_action(request, settings, monkeypatch):
    case, user, staff, verifier, other, client, receipt, person, held = prepared(
        request, settings, monkeypatch
    )
    proposal = plan(case, user)
    confirm(client, receipt, proposal)
    fresh(case, user, staff, verifier, other)
    version = case.version
    key = uuid.uuid4()
    barrier = Barrier(2)

    def run():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return execute(actor, case.pk, key, version, proposal.pk, REASON).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(run) for _ in range(2)]
        assert [job.result(timeout=30) for job in jobs] == [proposal.pk, proposal.pk]
    assert PrivacyHoldReleaseProposal.objects.filter(released_at__isnull=False).count() == 1
    case.refresh_from_db()
    assert case.version == version + 1
    held.refresh_from_db()
    assert not held.active


def test_mobile_proposal_receipt_and_execution_keep_publication_private(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    from apps.core.mfa import encrypt

    settings.DEBUG = True
    case, user, staff, verifier, other, client, receipt, person, held = prepared(
        request, settings, monkeypatch
    )
    secret = pyotp.random_base32()
    user.mfa_secret_encrypted = encrypt(secret)
    user.save(update_fields=["mfa_secret_encrypted"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    path = f"/en/moderation/rights/{case.pk}/publication-hold/release/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + path)
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record reviewed release action", exact=True).click()
            expect(page.locator("article")).to_have_count(1)
            state = context.storage_state()
            anonymous = browser.new_context(viewport={"width": 390, "height": 844})
            public = anonymous.new_page()
            public.goto(live_server.url + receipt)
            public.locator("[name=received]").check()
            public.get_by_role("button", name="Record response receipt", exact=True).click()
            expect(public.get_by_text("Receipt recorded", exact=False)).to_be_visible()
        finally:
            browser.close()
    proposal = PrivacyHoldReleaseProposal.objects.get()
    fresh(case, user, staff, verifier, other)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(
                storage_state=state, viewport={"width": 390, "height": 844}
            )
            page = context.new_page()
            page.goto(live_server.url + path)
            page.locator("[name=operation]").select_option("execute")
            page.locator("[name=proposal_id]").fill(str(proposal.pk))
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record reviewed release action", exact=True).click()
            expect(page.get_by_text("Release recorded", exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Release recorded", exact=False)).to_be_visible()
            assert page.locator("[name=reason]").count() == 0
        finally:
            browser.close()
    held.refresh_from_db()
    assert not held.active
    case.refresh_from_db()
    assert case.status == "reviewing"
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404
