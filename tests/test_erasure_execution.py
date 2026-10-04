import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_erasure_plans import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken, RecoveryCode, User
from apps.listings.models import Favorite
from apps.safety.crypto import cipher, seal, unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare as inventory
from apps.safety.erasure_plans import record
from apps.safety.models import ErasureExecution, RightsAction, RightsExport, RightsExportImage

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Execute selected scoped deletion after synthetic independent identity assessment"
PURPOSES = ["authentication", "account_preferences", "transient_copy"]


def plan_fixture(request, settings, monkeypatch):
    case, user, staff, client, receipt, person, _, decisions = prepared(
        request, settings, monkeypatch
    )
    subject = person.subject
    AccountToken.objects.create(
        user=subject,
        purpose="reset",
        digest="f" * 64,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    RecoveryCode.objects.create(user=subject, digest="e" * 64)
    Favorite.objects.create(user=subject, listing=person.listing)
    outsider = User.objects.get(username="fixture-v1-visitor")
    Favorite.objects.create(user=outsider, listing=person.listing)
    photo = person.listing.approved_revision.photos.first()
    action = RightsAction.objects.create(
        key=uuid.uuid4(),
        request=case,
        actor=user,
        expected_version=case.version,
        operation="export",
        payload_digest="f" * 64,
        encrypted_reason=seal(
            {"reason": "Synthetic stored snapshot fixture, not a released access copy"}
        ),
    )
    proof = case.proofs.latest("created_at")
    stored = RightsExport.objects.create(
        action=action,
        proof=proof,
        person=person,
        case_version=case.version,
        manager_version=person.manager_version,
        subject_snapshot=str(subject.pk),
        channel_digest=case.receipt_digest,
        encrypted_payload=seal({"synthetic_snapshot": True}),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    image = RightsExportImage.objects.create(
        export=stored,
        photo=photo,
        encrypted_content=cipher().encrypt(b"synthetic snapshot contents").decode(),
    )
    snapshot = inventory(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Prepare current inventory with synthetic account and copy records",
    )
    selected = [
        row | {"operation": "erase", "review_on": None} if row["purpose"] in PURPOSES else row
        for row in decisions
    ]
    plan = record(user, case.pk, snapshot.pk, uuid.uuid4(), case.version, selected)
    return case, user, staff, client, receipt, person, plan, stored, image, outsider


def payload(case):
    return {
        "key": uuid.uuid4(),
        "version": case.version,
        "purposes": PURPOSES,
        "reason": REASON,
        "confirmed": True,
    }


def test_actual_scoped_deletion_replay_isolated_sources_and_sessions(
    request, settings, monkeypatch
):
    case, user, staff, client, receipt, person, plan, stored, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    subject = person.subject
    old = Client()
    old.force_login(subject)
    assert old.get("/en/favorites/").status_code == 200
    listing_status = person.listing.status
    source_photos = person.listing.revisions.first().photos.count()
    due = case.initial_due_at
    path = f"/en/moderation/rights/{case.pk}/erasure-execute/{plan.pk}/"
    data = payload(case)
    assert staff.post(path, data).status_code == 200
    assert staff.post(path, data).status_code == 200
    execution = ErasureExecution.objects.get()
    result = unseal(execution.encrypted_result)
    assert result["partial"] and result["identity_simulated"]
    assert (
        result["tokens_deleted"]
        == result["recovery_codes_deleted"]
        == result["favorites_deleted"]
        == 1
    )
    assert result["copies_cleared"] == result["images_cleared"] == 1
    assert (
        not AccountToken.objects.filter(user=subject).exists()
        and not RecoveryCode.objects.filter(user=subject).exists()
    )
    assert (
        not Favorite.objects.filter(user=subject).exists()
        and Favorite.objects.filter(user=outsider).count() == 1
    )
    stored.refresh_from_db()
    image.refresh_from_db()
    person.refresh_from_db()
    case.refresh_from_db()
    assert stored.purged_at and not stored.encrypted_payload and not image.encrypted_content
    assert (
        person.listing.status == listing_status
        and person.listing.revisions.first().photos.count() == source_photos
    )
    assert (
        case.status == "reviewing"
        and case.scope_status == "unverified"
        and case.initial_due_at == due
    )
    assert person.rights_version == 2
    assert old.get("/en/favorites/").status_code == 302
    assert REASON.encode() not in client.get(receipt).content
    assert (
        RightsAction.objects.filter(pk=stored.action_id).exists()
        and execution.proof_id == stored.proof_id
    )
    assert staff.post(path, data | {"reason": REASON + " Changed"}).status_code == 409
    assert staff.post(path, payload(case)).status_code == 409


def test_no_deletion_with_stale_plan_review_choice_scope_csrf_or_production(
    request, settings, monkeypatch
):
    case, user, staff, _, _, person, plan, stored, _, _ = plan_fixture(
        request, settings, monkeypatch
    )
    path = f"/en/moderation/rights/{case.pk}/erasure-execute/{plan.pk}/"
    data = payload(case)
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert staff.post(path, data | {"confirmed": False}).status_code == 400
    assert staff.post(path, data | {"purposes": ["profile"]}).status_code == 400
    with pytest.raises(ValidationError):
        execute(user, case.pk, plan.pk, **(data | {"purposes": ["publication"]}))
    settings.PRODUCTION = True
    assert staff.post(path, data).status_code == 409
    settings.PRODUCTION = False
    person.alias += " changed"
    person.save(update_fields=["alias"])
    assert staff.post(path, data).status_code == 409
    stored.refresh_from_db()
    assert (
        stored.encrypted_payload and not stored.purged_at and not ErasureExecution.objects.exists()
    )
    assert AccountToken.objects.filter(user=person.subject).exists()


def test_execution_concurrent_same_key_has_one_effect(request, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    case, user, _, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    data = payload(case)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return execute(actor, case.pk, plan.pk, **data).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(worker) for _ in range(2)]
        assert results[0].result(timeout=30) == results[1].result(timeout=30)
    assert ErasureExecution.objects.count() == 1


def test_mobile_partial_execution_reports_open_request(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
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
            for purpose in PURPOSES:
                page.locator(f"[name=purposes][value={purpose}]").check()
            page.locator("[name=reason]").fill(REASON)
            page.locator("[name=confirmed]").check()
            page.get_by_role("button", name="Execute confirmed scoped erasure", exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
            )
            page.goto(page.url)
            assert page.get_by_role("status").count() == 0
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing" and ErasureExecution.objects.count() == 1


def test_inflight_favorite_cannot_recreate_erased_preferences(request, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from django.db import close_old_connections, connections

    from apps.core.models import Person
    from apps.listings import favorites

    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    target = Person.objects.get(individual__username="fixture-v1-individual").listing
    client = Client()
    client.force_login(person.subject)
    assert client.get("/en/favorites/").status_code == 200
    reached, resume = Event(), Event()
    visible = favorites.publicly_visible

    def wait_after_gate(listing):
        result = visible(listing)
        reached.set()
        assert resume.wait(timeout=30)
        return result

    monkeypatch.setattr(favorites, "publicly_visible", wait_after_gate)

    def add():
        close_old_connections()
        try:
            return client.post(f"/en/listing/{target.pk}/favorite/").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(add)
        try:
            assert reached.wait(timeout=15)
            execute(actor, case.pk, plan.pk, **payload(case))
        finally:
            resume.set()
        assert future.result(timeout=30) == 409
    assert not Favorite.objects.filter(user=person.subject).exists()


def test_person_privacy_version_revokes_other_case_preview(request, settings):
    from test_rights_exports import prepared as access_case

    from apps.safety.rights_exports import preview

    case, actor, _, _, _, person = access_case(request, settings)
    preview(actor, case.pk, case.version, "Review current independent access request")
    person.rights_version += 1
    person.save(update_fields=["rights_version"])
    with pytest.raises(ValidationError):
        preview(actor, case.pk, case.version, "Reject outdated independent access authorization")
    case.refresh_from_db()
    assert case.scope_status == "simulated_passed"


def test_person_privacy_version_revokes_existing_copy_download(request, settings):
    from test_rights_exports import make_copy, url
    from test_rights_exports import prepared as access_case

    case, actor, _, client, receipt, person = access_case(request, settings)
    export = make_copy(case, actor)
    path = url(receipt, export)
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 200
    person.rights_version += 1
    person.save(update_fields=["rights_version"])
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    export.refresh_from_db()
    assert export.encrypted_payload and export.purged_at is None
