import hashlib
import json
import shutil
import uuid

import pyotp
import pytest
from django.core.files.base import ContentFile
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_erasure_execution import payload, plan_fixture
from test_photos import raw_image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import Person, User
from apps.mediafiles.erasure import erase_due_media
from apps.mediafiles.models import Blob, MediaErasure, Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.models import ErasureExecution
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch, mixed=False):
    case, actor, staff, client, receipt, person, previous, _, _, _ = plan_fixture(
        request, settings, monkeypatch
    )
    shared = person.listing.approved_revision.photos.first().blob
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    peer_photo = Photo.objects.create(revision=peer.listing.revisions.first(), blob=shared)
    exclusive = None
    if mixed:
        raw = raw_image(seed=953)
        exclusive = Blob.objects.create(sha256=hashlib.sha256(raw).hexdigest(), status="ready")
        exclusive.original.save(str(uuid.uuid4()), ContentFile(raw))
        Photo.objects.create(revision=person.listing.approved_revision, blob=exclusive)
    inventory = prepare(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review shared file references for scoped redaction",
    )
    decisions = unseal(previous.encrypted_decisions)["decisions"]
    decisions = [
        row | {"operation": "redact", "review_on": None} if row["purpose"] == "media" else row
        for row in decisions
    ]
    plan = record(actor, case.pk, inventory.pk, uuid.uuid4(), case.version, decisions)
    return case, actor, staff, person, plan, shared, peer_photo, exclusive


def test_detach_shared_references_preserves_peer_files_and_audit_ids(
    request, settings, monkeypatch
):
    case, actor, _, person, plan, shared, peer_photo, _ = prepared(request, settings, monkeypatch)
    before = list(
        Photo.objects.filter(revision__listing__person=person).values_list("pk", flat=True)
    )
    original, derivative, sha = shared.original.name, shared.derivative.name, shared.sha256
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    own = Photo.objects.filter(revision__listing__person=person)
    assert list(own.values_list("pk", flat=True)) == before
    assert not own.filter(blob=shared).exists() and not own.filter(removed_at__isnull=True).exists()
    assert all(photo.blob.status == "erased" and not photo.blob.original for photo in own)
    peer_photo.refresh_from_db()
    shared.refresh_from_db()
    assert peer_photo.blob_id == shared.pk and peer_photo.removed_at is None
    assert shared.status == "ready" and shared.sha256 == sha
    assert shared.original.storage.exists(original) and shared.derivative.storage.exists(derivative)
    assert not MediaErasure.objects.exists() and erase_due_media() == 0
    result = unseal(execution.encrypted_result)
    assert result["media_refs_detached"] == len(before) and result["exclusive_media_pending"] == 0
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_mixed_scope_can_then_erase_exclusive_file_with_fresh_identity_and_plan(
    request, settings, monkeypatch
):
    case, actor, staff, person, plan, shared, peer_photo, exclusive = prepared(
        request, settings, monkeypatch, mixed=True
    )
    first = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    result = unseal(first.encrypted_result)
    assert result["exclusive_media_pending"] == 1 and "media" in result["pending_purposes"]
    exclusive.refresh_from_db()
    original = exclusive.original.name
    assert exclusive.status == "ready" and exclusive.original.storage.exists(original)
    case.refresh_from_db()
    read(staff, case)
    proof = start(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review exclusive media left after shared reference redaction",
    )
    case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
    other = Client()
    other.force_login(verifier)
    session = other.session
    session["mfa_version"] = verifier.mfa_version
    session.save()
    read(other, case)
    receive_event(
        verifier,
        simulate_event(
            proof.pk,
            uuid.uuid4(),
            case.version,
            "passed",
            "Independent synthetic scope assessment of remaining exclusive media",
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    inventory = prepare(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Inventory remaining exclusive media after independent check",
    )
    decisions = [
        row | {"operation": "erase"} if row["purpose"] == "media" else row
        for row in unseal(plan.encrypted_decisions)["decisions"]
    ]
    final_plan = record(actor, case.pk, inventory.pk, uuid.uuid4(), case.version, decisions)
    execute(actor, case.pk, final_plan.pk, **(payload(case) | {"purposes": ["media"]}))
    assert erase_due_media() == 1
    assert not exclusive.original.storage.exists(original)
    shared.refresh_from_db()
    peer_photo.refresh_from_db()
    assert shared.status == "ready" and peer_photo.blob_id == shared.pk
    assert shared.original.storage.exists(shared.original.name)


def test_mobile_reviewed_shared_media_redaction(
    live_server, request, settings, monkeypatch, tmp_path
):
    settings.DEBUG = True
    case, _, _, _, plan, _, _, _ = prepared(request, settings, monkeypatch)
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
            page.locator("[name=purposes][value=media]").check()
            page.locator("[name=reason]").fill(
                "Execute reviewed shared reference redaction for synthetic subject"
            )
            page.locator("[name=confirmed]").check()
            page.get_by_role("button", name="Execute confirmed scoped erasure", exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
            )
            assert "Shared references detached" in page.locator("main").inner_text()
            page.reload()
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
            )
            page.goto(page.url)
            assert page.get_by_role("status").count() == 0
        finally:
            browser.close()
    assert ErasureExecution.objects.filter(plan=plan).count() == 1


def test_concurrent_redaction_replay_creates_one_empty_marker(request, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    case, actor, _, _, plan, _, _, _ = prepared(request, settings, monkeypatch)
    key, barrier = uuid.uuid4(), Barrier(2)
    before = Blob.objects.filter(status="erased").count()

    def worker():
        close_old_connections()
        try:
            user = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return execute(
                user, case.pk, plan.pk, **(payload(case) | {"key": key, "purposes": ["media"]})
            ).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        assert futures[0].result(timeout=30) == futures[1].result(timeout=30)
    assert Blob.objects.filter(status="erased").count() == before + 1
    assert ErasureExecution.objects.filter(plan=plan).count() == 1


def test_redaction_without_shared_references_does_not_withdraw_images(
    request, settings, monkeypatch
):
    from django.core.exceptions import ValidationError

    case, actor, _, _, _, person, prior, _, _, _ = plan_fixture(request, settings, monkeypatch)
    decisions = [
        row | {"operation": "redact", "review_on": None} if row["purpose"] == "media" else row
        for row in unseal(prior.encrypted_decisions)["decisions"]
    ]
    plan = record(actor, case.pk, prior.inventory_id, uuid.uuid4(), case.version, decisions)
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    assert Photo.objects.filter(revision__listing__person=person, removed_at__isnull=True).exists()
    assert not ErasureExecution.objects.exists()
