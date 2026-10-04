import hashlib
import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

import pyotp
import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, PhoneChallenge, RepresentationAction, RepresentationInvitation
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record

pytestmark = pytest.mark.django_db(transaction=True)
SELECTED = ["contact", "representation", "shared_contact_review"]


def prepared(request, settings, monkeypatch):
    case, actor, staff, _, _, person, prior, _, _, _ = plan_fixture(request, settings, monkeypatch)
    code, raw = "345678", "synthetic-consent-token-" + uuid.uuid4().hex
    challenge = PhoneChallenge.objects.create(
        person=person,
        manager_version=person.manager_version,
        person_rights_version=person.rights_version,
        phone=person.phone_claim.phone,
        digest=salted_hmac("phone-otp", code, algorithm="sha256").hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    invitation = RepresentationInvitation.objects.create(
        person=person,
        email=person.subject.email,
        manager_version=person.manager_version,
        person_rights_version=person.rights_version,
        digest=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=1),
    )
    inventory = prepare(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review own contact challenges and pending representation invitations",
    )
    decisions = [
        row
        | {
            "operation": "redact" if row["purpose"] == "shared_contact_review" else "erase",
            "review_on": None,
        }
        if row["purpose"] in SELECTED
        else row
        for row in unseal(prior.encrypted_decisions)["decisions"]
    ]
    plan = record(actor, case.pk, inventory.pk, uuid.uuid4(), case.version, decisions)
    return case, actor, staff, person, plan, challenge, invitation, code, raw


def manager_client(person):
    client = Client()
    client.force_login(person.agency.owner)
    session = client.session
    session["mfa_version"] = person.agency.owner.mfa_version
    session.save()
    return client


def test_delete_codes_and_detach_phone_preserves_other_model_and_consent_evidence(
    request, settings, monkeypatch
):
    case, actor, _, person, plan, challenge, invitation, _, _ = prepared(
        request, settings, monkeypatch
    )
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    claim = person.phone_claim
    peer.phone_claim = claim
    peer.save(update_fields=["phone_claim"])
    # Shared-state change requires a fresh inventory/plan.
    inventory = prepare(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review shared agency phone association without deleting agency record",
    )
    plan = record(
        actor,
        case.pk,
        inventory.pk,
        uuid.uuid4(),
        case.version,
        unseal(plan.encrypted_decisions)["decisions"],
    )
    peer_before = list(peer.listing.revisions.values())
    grants = RepresentationAction.objects.filter(person=person).count()
    result = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": SELECTED}))
    person.refresh_from_db()
    peer.refresh_from_db()
    claim.refresh_from_db()
    assert person.phone_claim_id is None and peer.phone_claim_id == claim.pk and claim.phone
    assert not PhoneChallenge.objects.filter(pk=challenge.pk).exists()
    assert not RepresentationInvitation.objects.filter(pk=invitation.pk).exists()
    assert all(
        not revision.phone and not revision.whatsapp for revision in person.listing.revisions.all()
    )
    assert list(peer.listing.revisions.values()) == peer_before
    assert RepresentationAction.objects.filter(person=person).count() == grants
    data = unseal(result.encrypted_result)
    assert data["phone_association_detached"] and data["phone_challenges_deleted"] == 1
    assert data["representation_invitations_deleted"] == 1
    case.refresh_from_db()
    assert case.status == "reviewing"


@pytest.mark.parametrize("operation", ["confirm", "start", "invite", "accept"])
def test_inflight_contact_operation_cannot_recreate_erased_codes(
    request, settings, monkeypatch, operation
):
    from apps.core import verification

    case, actor, _, person, plan, challenge, invitation, code, raw = prepared(
        request, settings, monkeypatch
    )
    client = manager_client(person)
    reached, resume = Event(), Event()
    lock = verification.locked_manager_person
    person_lock = Person.objects.select_for_update

    def pause():
        reached.set()
        assert resume.wait(timeout=30)

    def manager_lock(user, person_id):
        pause()
        return lock(user, person_id)

    monkeypatch.setattr(verification, "locked_manager_person", manager_lock)
    if operation == "accept":
        client = Client()
        client.force_login(person.subject)

        # Acceptance locks Person directly. Pause only the callback's thread.
        def select_for_update(*args, **kwargs):
            import threading

            if threading.current_thread().name.startswith("contact_callback"):
                pause()
            return person_lock(*args, **kwargs)

        monkeypatch.setattr(Person.objects, "select_for_update", select_for_update)
    endpoints = {
        "confirm": (f"/en/phone/{challenge.pk}/confirm/", {"code": code}),
        "start": (f"/en/person/{person.pk}/phone/", {"phone": "600123456"}),
        "invite": (f"/en/person/{person.pk}/consent/invite/", {"email": person.subject.email}),
        "accept": (
            f"/en/representation/{invitation.pk}/{raw}/",
            {"authorize": "on", "version": "dev-1"},
        ),
    }
    path, data = endpoints[operation]

    def worker():
        close_old_connections()
        try:
            return client.post(path, data).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="contact_callback") as pool:
        future = pool.submit(worker)
        try:
            assert reached.wait(timeout=15)
            execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": SELECTED}))
        finally:
            resume.set()
        assert future.result(timeout=30) == 409
    assert not PhoneChallenge.objects.filter(person=person).exists()
    assert not RepresentationInvitation.objects.filter(person=person).exists()
    person.refresh_from_db()
    assert person.phone_claim_id is None


def test_mobile_contact_scoped_execution(live_server, request, settings, monkeypatch, tmp_path):
    settings.DEBUG = True
    case, _, _, _, plan, _, _, _, _ = prepared(request, settings, monkeypatch)
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
            page.goto(
                live_server.url + f"/en/moderation/rights/{case.pk}/erasure-execute/{plan.pk}/"
            )
            for purpose in SELECTED:
                page.locator(f"[name=purposes][value={purpose}]").check()
            page.locator("[name=reason]").fill(
                "Execute reviewed scoped deletion of synthetic codes and phone association"
            )
            page.locator("[name=confirmed]").check()
            page.get_by_role("button", name="Execute confirmed scoped erasure", exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
            )
            page.goto(page.url)
            assert page.get_by_role("status").count() == 0
        finally:
            browser.close()


def test_phone_redaction_invalidates_retained_codes_but_new_explicit_request_is_current(
    request, settings, monkeypatch
):
    from django.core import mail

    case, actor, _, person, plan, challenge, invitation, code, raw = prepared(
        request, settings, monkeypatch
    )
    execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["shared_contact_review"]}))
    client = manager_client(person)
    assert client.post(f"/en/phone/{challenge.pk}/confirm/", {"code": code}).status_code == 400
    subject = Client()
    subject.force_login(person.subject)
    assert (
        subject.post(
            f"/en/representation/{invitation.pk}/{raw}/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 409
    )
    assert PhoneChallenge.objects.filter(pk=challenge.pk).exists()
    assert RepresentationInvitation.objects.filter(pk=invitation.pk).exists()
    response = client.post(f"/en/person/{person.pk}/phone/", {"phone": "600123456"})
    assert response.status_code == 302
    current = PhoneChallenge.objects.filter(person=person).exclude(pk=challenge.pk).get()
    person.refresh_from_db()
    assert current.person_rights_version == person.rights_version == 2
    assert client.post(response.url, {"code": mail.outbox[-1].body}).status_code == 302
    assert all(not revision.phone for revision in person.listing.revisions.all())
