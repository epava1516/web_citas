import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.erasure_inventory import prepare as inventory
from apps.safety.erasure_plans import record
from apps.safety.models import ErasurePlan

pytestmark = pytest.mark.django_db(transaction=True)
BASIS = "Synthetic basis awaiting independent legal review before any execution"
REASON = "Synthetic minimized per-purpose assessment, without third-party identities"
SCOPE = "Only this subject's scoped resources, excluding other models and managers"


def prepared(request, settings, monkeypatch, subject_username="fixture-v1-model-a"):
    case, user, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "erase", subject_username=subject_username
    )
    snapshot = inventory(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review scoped resources before per-purpose decisions",
    )
    manifest = unseal(snapshot.encrypted_manifest)
    purposes = sorted({row["purpose"] for row in manifest["entries"]})
    decisions = [
        {
            "purpose": purpose,
            "operation": "review",
            "basis": BASIS,
            "reason": REASON,
            "scope": SCOPE,
            "review_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
        }
        for purpose in purposes
    ]
    return case, user, staff, client, receipt, person, snapshot, decisions


def form_payload(case, decisions, key=None):
    data = {
        "key": key or uuid.uuid4(),
        "version": case.version,
        "decisions-TOTAL_FORMS": len(decisions),
        "decisions-INITIAL_FORMS": len(decisions),
        "decisions-MIN_NUM_FORMS": 0,
        "decisions-MAX_NUM_FORMS": len(decisions),
    }
    for index, decision in enumerate(decisions):
        for field, value in decision.items():
            data[f"decisions-{index}-{field}"] = value or ""
    return data


def test_plan_is_encrypted_scoped_and_replay_keeps_request_source_and_proof(
    request, settings, monkeypatch
):
    case, user, staff, client, receipt, person, snapshot, decisions = prepared(
        request, settings, monkeypatch
    )
    original = case.version, case.scope_status, person.listing.status, person.manager_version
    path = f"/en/moderation/rights/{case.pk}/erasure-plan/{snapshot.pk}/"
    assert staff.get(path).status_code == 200
    payload = form_payload(case, decisions)
    response = staff.post(path, payload)
    assert response.status_code == 200 and response.context["recorded"]
    assert staff.post(path, payload).status_code == 200 and ErasurePlan.objects.count() == 1
    plan = ErasurePlan.objects.get()
    body = unseal(plan.encrypted_decisions)
    assert body["decisions"] == decisions and not body["execution_ready"]
    assert plan.review_on == timezone.localdate() + timedelta(days=30)
    assert REASON not in plan.encrypted_decisions and plan.source_digest == snapshot.source_digest
    case.refresh_from_db()
    person.refresh_from_db()
    assert (
        case.version,
        case.scope_status,
        person.listing.status,
        person.manager_version,
    ) == original
    assert BASIS.encode() not in staff.get(path).content
    assert REASON.encode() not in client.get(receipt).content
    assert (
        staff.post(path, payload | {"decisions-0-reason": REASON + " Changed"}).status_code == 409
    )


def test_omissions_duplicate_purposes_shared_phone_and_stale_source_are_rejected(
    request, settings, monkeypatch
):
    case, user, staff, _, _, person, snapshot, decisions = prepared(request, settings, monkeypatch)

    def attempt(value):
        return record(user, case.pk, snapshot.pk, uuid.uuid4(), case.version, value)

    with pytest.raises(ValidationError):
        attempt(decisions[:-1])
    with pytest.raises(ValidationError):
        attempt(decisions[:-1] + [decisions[0]])
    bad = [
        row | {"purpose": "another_person"} if index == 0 else row
        for index, row in enumerate(decisions)
    ]
    with pytest.raises(ValidationError):
        attempt(bad)
    shared = [
        row | {"operation": "erase", "review_on": None}
        if row["purpose"] == "shared_contact_review"
        else row
        for row in decisions
    ]
    with pytest.raises(ValidationError):
        attempt(shared)
    invalid_date = [
        row | {"review_on": (timezone.localdate() + timedelta(days=366)).isoformat()}
        for row in decisions
    ]
    with pytest.raises(ValidationError):
        attempt(invalid_date)
    assert not ErasurePlan.objects.exists()
    person.alias = "Scoped alias changed after inventory"
    person.save(update_fields=["alias"])
    path = f"/en/moderation/rights/{case.pk}/erasure-plan/{snapshot.pk}/"
    assert staff.post(path, form_payload(case, decisions)).status_code == 409
    with pytest.raises(ValidationError):
        attempt(decisions)
    assert not ErasurePlan.objects.exists()


def test_permissions_csrf_disabled_identity_and_foreign_inventory(request, settings, monkeypatch):
    case, user, staff, _, _, person, snapshot, decisions = prepared(request, settings, monkeypatch)
    path = f"/en/moderation/rights/{case.pk}/erasure-plan/{snapshot.pk}/"
    payload = form_payload(case, decisions)
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    user.user_permissions.remove(Permission.objects.get(codename="execute_rights_request"))
    assert staff.post(path, payload).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="execute_rights_request"))
    settings.PRODUCTION = True
    assert staff.get(path).status_code == 409
    settings.PRODUCTION = False
    assert (
        staff.get(f"/en/moderation/rights/{uuid.uuid4()}/erasure-plan/{snapshot.pk}/").status_code
        == 404
    )
    assert staff.post(path, payload | {"decisions-TOTAL_FORMS": 9999}).status_code == 400
    proof = snapshot.proof
    proof.scope = "access"
    proof.save(update_fields=["scope"])
    assert staff.post(path, payload).status_code == 409
    assert not ErasurePlan.objects.exists()


def test_concurrent_plan_same_key_records_once(request, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    case, user, _, _, _, _, snapshot, decisions = prepared(request, settings, monkeypatch)
    key = uuid.uuid4()
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return record(actor, case.pk, snapshot.pk, key, case.version, decisions).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(worker) for _ in range(2)]
        assert results[0].result(timeout=30) == results[1].result(timeout=30)
    assert ErasurePlan.objects.count() == 1


def test_mobile_inventory_to_per_purpose_plan(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, _, _, _ = prepared(request, settings, monkeypatch)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    review_date = (timezone.localdate() + timedelta(days=30)).isoformat()
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
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/erasure-inventory/")
            page.locator("[name=purpose]").fill(
                "Prepare a current inventory for scoped retention decisions"
            )
            page.get_by_role("button", name="Record and inspect inventory", exact=True).click()
            page.get_by_role(
                "link", name="Review erasure and retention decisions", exact=True
            ).click()
            for fieldset in page.locator("fieldset").all():
                fieldset.locator("select").select_option("review")
                fieldset.locator("[name$=-scope]").fill(SCOPE)
                fieldset.locator("[name$=-basis]").fill(BASIS)
                fieldset.locator("[name$=-reason]").fill(REASON)
                fieldset.locator("[name$=-review_on]").fill(review_date)
            page.get_by_role("button", name="Record per-purpose decisions", exact=True).click()
            expect(page.get_by_role("status")).to_have_text("Plan recorded; execution pending")
            page.goto(page.url)
            assert page.get_by_role("status").count() == 0 and BASIS not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing" and ErasurePlan.objects.count() == 1


def test_mixed_decisions_record_intent_without_deleting_credentials_or_preferences(
    request, settings, monkeypatch
):
    from apps.core.models import AccountToken, RecoveryCode
    from apps.listings.models import Favorite

    case, user, _, _, _, person, _, decisions = prepared(request, settings, monkeypatch)
    AccountToken.objects.create(
        user=person.subject,
        purpose="reset",
        digest="f" * 64,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    RecoveryCode.objects.create(user=person.subject, digest="e" * 64)
    Favorite.objects.create(user=person.subject, listing=person.listing)
    snapshot = inventory(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review fresh inventory after synthetic account preferences",
    )
    selected = []
    for row in decisions:
        if row["purpose"] in {
            "authentication",
            "account_preferences",
            "transient_copy",
            "publication",
        }:
            selected.append(row | {"operation": "erase", "review_on": None})
        elif row["purpose"] in {"profile", "media", "shared_contact_review"}:
            selected.append(row | {"operation": "redact", "review_on": None})
        else:
            selected.append(
                row
                | {
                    "operation": "retain",
                    "review_on": (timezone.localdate() + timedelta(days=7)).isoformat(),
                }
            )
    plan = record(user, case.pk, snapshot.pk, uuid.uuid4(), case.version, selected)
    assert plan.review_on == timezone.localdate() + timedelta(days=7)
    assert unseal(plan.encrypted_decisions)["decisions"] == selected
    assert AccountToken.objects.filter(user=person.subject).count() == 1
    assert RecoveryCode.objects.filter(user=person.subject).count() == 1
    assert Favorite.objects.filter(user=person.subject).count() == 1
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_shared_media_and_other_account_responsibilities_prevent_global_erase(
    request, settings, monkeypatch
):
    from apps.core.models import Person
    from apps.mediafiles.models import Photo

    case, user, _, _, _, person, _, decisions = prepared(request, settings, monkeypatch)
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    photo = person.listing.approved_revision.photos.first()
    Photo.objects.create(
        revision=peer.listing.revisions.latest("created_at"), blob=photo.blob, position=7
    )
    subject = person.subject
    subject.is_staff = True
    subject.save(update_fields=["is_staff"])
    snapshot = inventory(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review fresh shared references and account responsibility",
    )
    manifest = unseal(snapshot.encrypted_manifest)
    assert manifest["account_has_other_responsibilities"] and any(
        row["shared_reference"] for row in manifest["media"]
    )
    for purpose in ["media", "account"]:
        selected = [
            row | {"operation": "erase", "review_on": None} if row["purpose"] == purpose else row
            for row in decisions
        ]
        with pytest.raises(ValidationError):
            record(user, case.pk, snapshot.pk, uuid.uuid4(), case.version, selected)
    assert not ErasurePlan.objects.exists()
