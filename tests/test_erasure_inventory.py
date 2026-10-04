import uuid

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import Person, User
from apps.mediafiles.models import Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_inventory import canonical, prepare, source_manifest
from apps.safety.models import ErasureInventory
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)
PURPOSE = "Review scoped resources and retention dependencies before erasure"


def values(case):
    return {"key": uuid.uuid4(), "version": case.version, "purpose": PURPOSE}


def test_scoped_encrypted_inventory_preserves_source_and_marks_shared_media(
    request, settings, monkeypatch
):
    case, user, staff, client, receipt, person = ready(request, settings, monkeypatch, "erase")
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    own_photo = person.listing.approved_revision.photos.first()
    Photo.objects.create(
        revision=peer.listing.revisions.latest("created_at"), blob=own_photo.blob, position=7
    )
    original = person.listing.status, person.manager_version, case.version, case.scope_status
    payload = values(case)
    path = f"/en/moderation/rights/{case.pk}/erasure-inventory/"
    assert staff.get(path).context["manifest"] is None
    result = staff.post(path, payload)
    assert result.status_code == 200
    manifest = result.context["manifest"]
    assert manifest["shared_phone"] and any(row["shared_reference"] for row in manifest["media"])
    assert not manifest["execution_ready"] and all(
        row["disposition"] == "review_required" for row in manifest["entries"]
    )
    assert str(peer.pk) not in canonical(manifest)
    assert person.subject.email not in canonical(
        manifest
    ) and own_photo.blob.sha256 not in canonical(manifest)
    inventory = ErasureInventory.objects.get()
    assert manifest == unseal(inventory.encrypted_manifest)
    assert "erasure-inventory-v1" not in inventory.encrypted_manifest
    assert inventory.source_digest == fingerprint(canonical(manifest))
    assert staff.post(path, payload).status_code == 200 and ErasureInventory.objects.count() == 1
    person.refresh_from_db()
    case.refresh_from_db()
    assert (
        person.listing.status,
        person.manager_version,
        case.version,
        case.scope_status,
    ) == original
    assert b"erasure-inventory-v1" not in client.get(receipt).content
    assert staff.get(path).context["manifest"] is None
    before = fingerprint(canonical(source_manifest(person)))
    peer.alias = "Changed unrelated peer alias"
    peer.save(update_fields=["alias"])
    assert fingerprint(canonical(source_manifest(person))) == before
    revision = person.listing.approved_revision
    revision.description += " Scoped description changed"
    revision.save(update_fields=["description"])
    assert fingerprint(canonical(source_manifest(person))) != before
    contact_before = fingerprint(canonical(source_manifest(person)))
    claim = person.phone_claim
    claim.verification_procedure = "changed-synthetic-procedure"
    claim.save(update_fields=["verification_procedure"])
    assert fingerprint(canonical(source_manifest(person))) != contact_before
    after_text = fingerprint(canonical(source_manifest(person)))
    revision.categories.clear()
    assert fingerprint(canonical(source_manifest(person))) != after_text


def test_inventory_rejects_wrong_scope_permissions_production_and_csrf(
    request, settings, monkeypatch
):
    case, user, staff, _, _, person = ready(request, settings, monkeypatch, "erase")
    path = f"/en/moderation/rights/{case.pk}/erasure-inventory/"
    payload = values(case)
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    owner = Client()
    owner.force_login(person.agency.owner)
    session = owner.session
    session["mfa_version"] = person.agency.owner.mfa_version
    session.save()
    assert owner.post(path, payload).status_code == 403
    permission = Permission.objects.get(codename="execute_rights_request")
    user.user_permissions.remove(permission)
    assert staff.post(path, payload).status_code == 403
    user.user_permissions.add(permission)
    settings.PRODUCTION = True
    assert staff.post(path, payload).status_code == 409
    settings.PRODUCTION = False
    proof = case.proofs.latest("created_at")
    proof.scope = "access"
    proof.save(update_fields=["scope"])
    assert staff.post(path, payload).status_code == 409
    assert not ErasureInventory.objects.exists()
    proof.scope = "erase"
    proof.save(update_fields=["scope"])
    prepare(User.objects.get(pk=user.pk), case.pk, **payload)
    assert (
        staff.post(
            path, payload | {"purpose": "Another conflicting purpose for the same operation"}
        ).status_code
        == 409
    )


def test_mobile_inventory_is_audited_and_not_disclosed_on_get(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, _ = ready(request, settings, monkeypatch, "erase")
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
                "Inspect current rights request before preparing erasure"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            page.get_by_role("link", name="Prepare erasure inventory", exact=True).click()
            page.locator("[name=purpose]").fill(PURPOSE)
            page.get_by_role("button", name="Record and inspect inventory", exact=True).click()
            expect(page.get_by_role("table")).to_be_visible()
            expect(page.get_by_text("core.User", exact=True)).to_be_visible()
            page.goto(page.url)
            assert page.get_by_role("table").count() == 0
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing" and ErasureInventory.objects.count() == 1


def test_concurrent_preparation_is_one_record_and_new_evidence_is_required(
    request, settings, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    from apps.safety.models import RightsAccess

    case, user, staff, _, _, person = ready(request, settings, monkeypatch, "erase")
    payload = values(case)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return prepare(actor, case.pk, **payload).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker) for _ in range(2)]
        assert futures[0].result(timeout=30) == futures[1].result(timeout=30)
    assert ErasureInventory.objects.count() == 1
    path = f"/en/moderation/rights/{case.pk}/erasure-inventory/"
    RightsAccess.objects.filter(request=case, actor=user).delete()
    assert staff.post(path, payload).status_code == 409
    assert ErasureInventory.objects.count() == 1
    person.refresh_from_db()
    assert person.listing.status == "published"
