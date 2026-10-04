import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_linking import link, ready

from apps.core.models import Person, User
from apps.safety.models import RightsProof, RightsProofEvent, RightsRequest
from apps.safety.rights_verification import authorized_proof, receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings):
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    case, user, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    path, linked = link(staff, case, person)
    assert staff.post(path, linked).status_code == 302
    staff.post(
        f"/en/moderation/rights/{case.pk}/",
        {"purpose": "Read current evidence before identity procedure"},
    )
    case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.mfa_enabled = True
    verifier.mfa_version = 1
    verifier.save(update_fields=["mfa_enabled", "mfa_version"])
    verifier.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "verify_rights_scope"])
    )
    other = Client()
    other.force_login(verifier)
    session = other.session
    session["mfa_version"] = verifier.mfa_version
    session.save()
    return case, user, staff, person, verifier, other


def payload(client, case, operation, **extra):
    path = f"/en/moderation/rights/{case.pk}/verification/"
    return path, {
        **client.get(path).context["form"].initial,
        "operation": operation,
        "reason": "Synthetic independent identity and scope procedure",
        **extra,
    }


def read(client, case):
    assert (
        client.post(
            f"/en/moderation/rights/{case.pk}/",
            {"purpose": "Independent review of latest evidence and scope"},
        ).status_code
        == 200
    )


def test_scoped_simulation_needs_independent_permission_and_current_evidence(request, settings):
    case, user, staff, person, verifier, other = prepared(request, settings)
    dates = case.received_at, case.initial_due_at
    path, submitted = payload(staff, case, "start")
    assert staff.post(path, submitted).status_code == 302
    assert staff.post(path, submitted).status_code == 302
    proof = RightsProof.objects.get()
    assert proof.scope == "representation" and proof.person_id == person.pk
    assert proof.provider == "simulator" and proof.procedure == "rights-simulator-v1"
    assert submitted["reason"] not in proof.encrypted_reason
    user.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    path, result = payload(staff, case, "result", outcome="passed")
    assert staff.post(path, result).status_code == 403
    path, result = payload(other, case, "result", outcome="passed")
    assert other.post(path, result).status_code == 409
    read(other, case)
    verifier.user_permissions.remove(Permission.objects.get(codename="verify_rights_scope"))
    assert other.post(path, result).status_code == 403
    verifier.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    assert other.post(path, result).status_code == 302
    assert other.post(path, result).status_code == 302
    case.refresh_from_db()
    proof.refresh_from_db()
    assert case.version == proof.case_version == 5
    assert case.scope_status == "simulated_passed" and proof.status == "passed"
    assert (case.received_at, case.initial_due_at) == dates
    assert authorized_proof(case, person, "representation").pk == proof.pk
    with pytest.raises(ValidationError):
        authorized_proof(case, person, "access")
    settings.PRODUCTION = True
    with pytest.raises(ValidationError):
        authorized_proof(case, person, "representation")
    with pytest.raises(PermissionDenied):
        receive_event(
            verifier,
            simulate_event(proof.pk, uuid.uuid4(), case.version, "passed", result["reason"]),
        )
    assert RightsProofEvent.objects.count() == 1


@pytest.mark.parametrize("outcome", ["pending", "failed"])
def test_incomplete_or_failed_proof_never_authorizes_rights(request, settings, outcome):
    case, user, _, person, verifier, other = prepared(request, settings)
    proof = start(user, case.pk, uuid.uuid4(), case.version, "Synthetic rights proof initiation")
    case.refresh_from_db()
    read(other, case)
    event = simulate_event(
        proof.pk, uuid.uuid4(), case.version, outcome, "Synthetic independent rights assessment"
    )
    receive_event(verifier, event)
    case.refresh_from_db()
    assert case.scope_status == "unverified"
    with pytest.raises(ValidationError):
        authorized_proof(case, person, case.kind)
    with pytest.raises(signing.BadSignature):
        receive_event(verifier, event + "tampered")


def test_manager_change_or_new_clarification_invalidates_proof(request, settings):
    case, user, _, person, verifier, other = prepared(request, settings)
    proof = start(user, case.pk, uuid.uuid4(), case.version, "Synthetic rights proof initiation")
    case.refresh_from_db()
    read(other, case)
    event = simulate_event(
        proof.pk, uuid.uuid4(), case.version, "passed", "Synthetic independent rights assessment"
    )
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    with pytest.raises(ValidationError):
        receive_event(verifier, event)
    assert not RightsProofEvent.objects.exists()
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version)
    RightsRequest.objects.filter(pk=case.pk).update(version=case.version + 1)
    # Controlled version drift represents an intervening clarification, not a proven identity.
    with pytest.raises(ValidationError):
        receive_event(verifier, event)
    assert not RightsProofEvent.objects.exists()


def test_disabled_adapter_and_production_reject_synthetic_checks(request, settings):
    case, _, staff, _, _, _ = prepared(request, settings)
    path = f"/en/moderation/rights/{case.pk}/verification/"
    settings.RIGHTS_VERIFICATION_BACKEND = "disabled"
    assert staff.get(path).status_code == 503
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    settings.PRODUCTION = True
    assert staff.get(path).status_code == 503
    assert not RightsProof.objects.exists()


def test_two_simulated_results_only_consume_version_once(request, settings):
    case, user, _, _, verifier, other = prepared(request, settings)
    proof = start(user, case.pk, uuid.uuid4(), case.version, "Synthetic rights proof initiation")
    case.refresh_from_db()
    read(other, case)
    event = simulate_event(
        proof.pk, uuid.uuid4(), case.version, "passed", "Synthetic independent rights assessment"
    )
    barrier = Barrier(2)

    def complete(_):
        close_old_connections()
        try:
            actor = User.objects.get(pk=verifier.pk)
            barrier.wait(timeout=10)
            return receive_event(actor, event).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(complete, range(2)))
    assert outcomes == [proof.pk, proof.pk]
    assert RightsProofEvent.objects.count() == 1
    case.refresh_from_db()
    assert case.version == 5


def test_mobile_operator_starts_explicit_simulation(live_server, request, settings, tmp_path):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, verifier, _ = prepared(request, settings)
    from apps.core.mfa import encrypt

    secret = pyotp.random_base32()
    verifier.mfa_secret_encrypted = encrypt(secret)
    verifier.save(update_fields=["mfa_secret_encrypted"])
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
            page.get_by_role("link", name="Identity and scope check", exact=True).click()
            expect(
                page.get_by_role("heading", name="Simulated rights verification", exact=True)
            ).to_be_visible()
            assert "No real identity" in page.content()
            page.locator("[name=operation]").select_option("start")
            page.locator("[name=reason]").fill(
                "Synthetic proportional procedure without identity documents"
            )
            page.get_by_role("button", name="Record simulated check", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            page.reload()
            assert "rights-private@example.invalid" not in page.content()
            independent = browser.new_page(viewport={"width": 390, "height": 844})
            independent.goto(live_server.url + "/en/account/login/")
            independent.locator("[name=email]").fill(verifier.email)
            independent.locator("[name=password]").fill(credentials["password"])
            independent.locator("button[type=submit]").click()
            independent.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            independent.locator("button[type=submit]").click()
            independent.goto(live_server.url + f"/en/moderation/rights/{case.pk}/")
            independent.locator("[name=purpose]").fill(
                "Independent review of latest scoped synthetic evidence"
            )
            independent.get_by_role("button", name="Record access and inspect", exact=True).click()
            independent.get_by_role("link", name="Identity and scope check", exact=True).click()
            independent.locator("[name=operation]").select_option("result")
            independent.locator("[name=outcome]").select_option("passed")
            independent.locator("[name=reason]").fill(
                "Independent synthetic verification, not real identity"
            )
            independent.get_by_role("button", name="Record simulated check", exact=True).click()
            expect(
                independent.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            independent.get_by_role("link", name="Identity and scope check", exact=True).click()
            assert "simulated_passed" in independent.content()
        finally:
            browser.close()
    assert RightsProof.objects.get().status == "passed"


def test_simulated_pass_requires_audited_delivery_of_all_clarification_pages(request, settings):
    from apps.safety.crypto import seal
    from apps.safety.models import RightsMessage
    from apps.safety.rights import fingerprint

    case, user, _, _, verifier, other = prepared(request, settings)
    # Synthetic history fixture: pagination evidence, not public intake or verified identity.
    RightsMessage.objects.bulk_create(
        [
            RightsMessage(
                key=uuid.uuid4(),
                request=case,
                expected_version=1,
                payload_digest=fingerprint(f"synthetic-{index}"),
                encrypted_payload=seal({"text": f"Synthetic clarification {index}"}),
            )
            for index in range(52)
        ]
    )
    proof = start(user, case.pk, uuid.uuid4(), case.version, "Synthetic rights proof initiation")
    case.refresh_from_db()
    inspect = f"/en/moderation/rights/{case.pk}/"
    first = other.post(inspect, {"purpose": "Read latest clarification page for identity review"})
    event = simulate_event(
        proof.pk, uuid.uuid4(), case.version, "passed", "Synthetic independent rights assessment"
    )
    with pytest.raises(ValidationError):
        receive_event(verifier, event)
    assert not RightsProofEvent.objects.exists()
    assert (
        other.post(
            inspect,
            {
                "purpose": "Read remaining clarification page for identity review",
                "message_before": first.context["next_message_cursor"],
            },
        ).status_code
        == 200
    )
    assert receive_event(verifier, event).status == "passed"
