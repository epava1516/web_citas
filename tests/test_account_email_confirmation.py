"""Real HTTP/PostgreSQL confirmation with explicit local simulated delivery."""

from datetime import timedelta
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from django.test import Client
from django.utils import timezone
from test_privacy_release import fresh
from test_rectification_review import REASON, independent_case
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import RightsAccountEmailConfirmation
from apps.safety.rectification_review import inspect, review
from apps.safety.rights_rectification import preview

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(
    request,
    settings,
    monkeypatch,
    *,
    with_receipt=False,
    changes=None,
    subject_username="fixture-v1-model-a",
):
    settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "simulator"
    result = independent_case(
        request,
        settings,
        monkeypatch,
        with_receipt=with_receipt,
        subject_username=subject_username,
        changes=changes
        or {
            "account": {
                "first_name": "Synthetic",
                "last_name": "Subject",
                "email": "new-subject@example.invalid",
            }
        },
    )
    case, actor, staff, person, proposal, path = result[:6]
    preview(
        actor, case.pk, case.version, "Inspect source before reviewing proposed account correction"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Inspect proposed account correction independently",
    )
    review(actor, case.pk, proposal.pk, uuid4(), case.version, "approved", REASON)
    original = proposal.action.actor
    verifier = Client()
    verifier.force_login(original)
    session = verifier.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, actor, staff, original, verifier)
    preview(
        actor, case.pk, case.version, "Inspect current account source after independent approval"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Inspect approved account changes with fresh scoped proof",
    )
    data = {"key": uuid4(), "version": case.version, "operation": "confirm_email", "reason": REASON}
    output = case, actor, staff, person, proposal, path, data
    return (*output, *result[6:]) if with_receipt else output


def test_audited_destination_confirmation_http_keeps_account_unchanged(
    request, settings, monkeypatch
):
    case, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    before = person.subject.email, person.subject.session_version, person.listing.revisions.count()
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    assert staff.post(path, data).status_code == 302
    assert RightsAccountEmailConfirmation.objects.count() == 1
    delivery = unseal(token.encrypted_delivery)
    assert delivery["simulation"] is True
    public_path = urlsplit(delivery["url"]).path
    raw = public_path.rstrip("/").split("/")[-1]
    assert raw not in token.encrypted_delivery
    anonymous = Client()
    exchanged = anonymous.get(public_path)
    assert exchanged.status_code == 302 and exchanged["Referrer-Policy"] == "no-referrer"
    clean_path = exchanged["Location"]
    page = anonymous.get(clean_path)
    assert page.status_code == 200 and b"new-subject@example.invalid" not in page.content
    assert raw.encode() not in page.content
    assert page["Referrer-Policy"] == "same-origin"
    assert "no-store" in page["Cache-Control"] and "noindex" in page["X-Robots-Tag"]
    token.refresh_from_db()
    assert token.confirmed_at is None
    csrf = Client(enforce_csrf_checks=True).post(clean_path, {"confirmed": "on"})
    assert csrf.status_code == 403
    assert anonymous.post(clean_path, {}).status_code == 400
    assert anonymous.post(clean_path, {"confirmed": "on"}).status_code == 200
    token.refresh_from_db()
    confirmed_at = token.confirmed_at
    assert confirmed_at and not token.encrypted_delivery
    assert anonymous.post(clean_path, {"confirmed": "on"}).status_code == 200
    token.refresh_from_db()
    assert token.confirmed_at == confirmed_at
    person.subject.refresh_from_db()
    assert (
        person.subject.email,
        person.subject.session_version,
        person.listing.revisions.count(),
    ) == before
    assert anonymous.get(public_path.replace(raw, "invalid-token")).status_code == 400
    RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert anonymous.post(clean_path, {"confirmed": "on"}).status_code == 400


def test_confirmation_delivery_is_disabled_and_source_changes_invalidate_link(
    request, settings, monkeypatch
):
    _, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    settings.PRODUCTION = True
    assert staff.post(path, data).status_code == 403
    assert not RightsAccountEmailConfirmation.objects.exists()
    settings.PRODUCTION = False
    settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "disabled"
    assert staff.post(path, data).status_code == 403
    settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "simulator"
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    public_path = urlsplit(unseal(token.encrypted_delivery)["url"]).path
    user = person.subject
    original_password = user.password
    user.set_password("Synthetic-source-changed-before-confirmation!847")
    user.save(update_fields=["password"])
    assert Client().get(public_path).status_code == 400
    assert (
        Client()
        .post(f"/en/safety/account-email-confirm/{token.pk}/", {"confirmed": "on"})
        .status_code
        == 400
    )
    token.refresh_from_db()
    assert token.confirmed_at is None

    user.password = original_password
    user.save(update_fields=["password"])
    token.proof.status = "pending"
    token.proof.save(update_fields=["status"])
    assert Client().get(public_path).status_code == 400
    assert (
        Client()
        .post(f"/en/safety/account-email-confirm/{token.pk}/", {"confirmed": "on"})
        .status_code
        == 400
    )
    token.refresh_from_db()
    assert token.confirmed_at is None


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_destination_confirmation_is_visible_and_persists(
    request, settings, monkeypatch, live_server, language
):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    _, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    public_path = urlsplit(unseal(token.encrypted_delivery)["url"]).path
    public_path = public_path.replace("/en/", f"/{language}/", 1)
    old_email = person.subject.email
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + public_path)
            page.reload()
            expect(page.locator('[name="confirmed"]')).to_be_visible()
            page.locator('[name="confirmed"]').check()
            page.get_by_role(
                "button",
                name="Confirm destination" if language == "en" else "Confirmar destino",
                exact=True,
            ).click()
            label = "Destination confirmed." if language == "en" else "Destino confirmado."
            expect(page.get_by_role("status")).to_contain_text(label)
            expect(page.locator("form")).to_have_count(0)
            page.reload()
            expect(page.get_by_role("status")).to_contain_text(label)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    token.refresh_from_db()
    person.subject.refresh_from_db()
    assert token.confirmed_at and not token.encrypted_delivery
    assert person.subject.email == old_email


def test_account_only_execution_consumes_confirmation_without_changing_listing(
    request, settings, monkeypatch
):
    from django.contrib.auth.models import Permission

    from apps.core.models import User
    from apps.safety.models import RightsRectificationManagerNotice
    from apps.safety.rectification_execution import execute, notify

    case, actor, staff, person, proposal, path, data, client, receipt = prepared(
        request, settings, monkeypatch, with_receipt=True
    )
    actor.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    actor = User.objects.get(pk=actor.pk)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    destination = Client()
    exchange = destination.get(urlsplit(unseal(token.encrypted_delivery)["url"]).path)
    assert destination.post(exchange["Location"], {"confirmed": "on"}).status_code == 200
    original = proposal.action.actor
    verifier = Client()
    verifier.force_login(original)
    session = verifier.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, actor, staff, original, verifier)
    preview(
        actor, case.pk, case.version, "Read account source before communication of approved changes"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Read approved account changes before communication",
    )
    notification = notify(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    assert (
        client.post(
            receipt + f"response/{notification.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )
    fresh(case, actor, staff, original, verifier)
    preview(
        actor, case.pk, case.version, "Read received correction source before account execution"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Read approved received account changes before execution",
    )
    listing = person.listing
    before = (
        listing.status,
        listing.lifecycle_version,
        listing.available_until,
        listing.revisions.count(),
    )
    old_session = person.subject.session_version
    key, version = uuid4(), case.version
    from django.core.exceptions import ValidationError

    from apps.core.accounts import send_token
    from apps.core.models import AccountToken
    from apps.safety.models import RightsRectificationExecution

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    from django.core import mail

    send_token(person.subject, "reset", "en")
    old_reset_path = urlsplit(mail.outbox[-1].body.splitlines()[-1]).path
    old_tokens = list(
        AccountToken.objects.filter(user=person.subject, used_at__isnull=True).values_list(
            "pk", flat=True
        )
    )
    logged_in = Client()
    logged_in.force_login(person.subject)
    logged_in.get("/health/")
    assert "_auth_user_id" in logged_in.session
    mfa_before = (
        person.subject.mfa_secret_encrypted,
        person.subject.mfa_version,
        person.subject.mfa_enabled,
    )
    token.refresh_from_db()
    for field, invalid in [
        ("confirmed_at", None),
        ("expires_at", timezone.now() - timedelta(seconds=1)),
        ("revoked_at", timezone.now()),
        ("consumed_at", timezone.now()),
    ]:
        original_value = getattr(token, field)
        RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(**{field: invalid})
        with pytest.raises(ValidationError):
            execute(actor, case.pk, proposal.pk, key, version, REASON)
        person.subject.refresh_from_db()
        assert person.subject.email != "new-subject@example.invalid"
        assert person.subject.session_version == old_session
        assert not RightsRectificationExecution.objects.exists()
        RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(**{field: original_value})
    settings.PRODUCTION = True
    with pytest.raises(ValidationError):
        execute(actor, case.pk, proposal.pk, key, version, REASON)
    settings.PRODUCTION = False
    result = execute(actor, case.pk, proposal.pk, key, version, REASON)
    assert not AccountToken.objects.filter(pk__in=old_tokens, used_at__isnull=True).exists()
    assert Client().get(old_reset_path).status_code == 400
    logged_in.get("/health/")
    assert "_auth_user_id" not in logged_in.session

    person.subject.refresh_from_db()
    listing.refresh_from_db()
    token.refresh_from_db()
    assert (
        person.subject.mfa_secret_encrypted,
        person.subject.mfa_version,
        person.subject.mfa_enabled,
    ) == mfa_before
    assert person.subject.email == "new-subject@example.invalid"
    assert person.subject.session_version == old_session + 1
    assert person.subject.email_verified_at == token.confirmed_at
    assert token.consumed_at and result.corrected_revision_id is None
    assert (
        listing.status,
        listing.lifecycle_version,
        listing.available_until,
        listing.revisions.count(),
    ) == before
    assert not RightsRectificationManagerNotice.objects.filter(execution=result).exists()
    assert execute(actor, case.pk, proposal.pk, key, version, REASON).pk == result.pk
    person.subject.refresh_from_db()
    assert person.subject.session_version == old_session + 1


def test_expired_confirmation_delivery_is_purged_without_erasing_audit(
    request, settings, monkeypatch
):
    from apps.safety.account_email_confirmation import purge_expired_delivery
    from apps.safety.tasks import purge_expired_account_confirmation_delivery

    case, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    user_state = person.subject.email, person.subject.session_version
    assert purge_expired_delivery() == 0
    token.refresh_from_db()
    assert token.encrypted_delivery
    RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    # Cleanup must remain possible after the delivery backend is disabled.
    settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "disabled"
    assert purge_expired_account_confirmation_delivery() == 1
    assert purge_expired_delivery() == 0
    token.refresh_from_db()
    case.refresh_from_db()
    person.subject.refresh_from_db()
    assert not token.encrypted_delivery and not token.confirmed_at and not token.consumed_at
    assert token.action_id and token.proof_id and token.source_digest and token.destination_digest
    assert (person.subject.email, person.subject.session_version) == user_state
    assert case.status == "reviewing"


@pytest.mark.parametrize("mixed", [False, True])
def test_name_correction_needs_no_new_mailbox_and_mixed_changes_preserve_review(
    request, settings, monkeypatch, mixed
):
    from django.contrib.auth.models import Permission

    from apps.core.models import User
    from apps.safety.rectification_execution import execute, notify

    changes = {
        "account": {"first_name": "Corrected synthetic name", "last_name": "Corrected surname"}
    }
    if mixed:
        changes["title"] = "Corrected synthetic listing title"
    case, actor, staff, person, proposal, _, _, client, receipt = prepared(
        request, settings, monkeypatch, with_receipt=True, changes=changes
    )
    actor.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    actor = User.objects.get(pk=actor.pk)
    notification = notify(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    assert (
        client.post(
            receipt + f"response/{notification.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )
    verifier = Client()
    original = proposal.action.actor
    verifier.force_login(original)
    session = verifier.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, actor, staff, original, verifier)
    preview(
        actor, case.pk, case.version, "Inspect received names correction source before execution"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Inspect received names correction proposal before execution",
    )
    listing = person.listing
    original_revision = listing.approved_revision
    before_title = original_revision.title
    before_listing = listing.status, listing.lifecycle_version, listing.available_until
    revision_count = listing.revisions.count()
    before_account = (
        person.subject.email,
        person.subject.email_verified_at,
        person.subject.session_version,
        person.subject.password,
    )
    # Names correction needs no mailbox delivery provider at all.
    settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "disabled"
    result = execute(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    person.subject.refresh_from_db()
    listing.refresh_from_db()
    original_revision.refresh_from_db()
    assert person.subject.first_name == changes["account"]["first_name"]
    assert person.subject.last_name == changes["account"]["last_name"]
    assert (
        person.subject.email,
        person.subject.email_verified_at,
        person.subject.session_version,
        person.subject.password,
    ) == before_account
    assert not RightsAccountEmailConfirmation.objects.exists()
    assert original_revision.title == before_title
    if mixed:
        corrected = result.corrected_revision
        assert corrected and corrected.title == changes["title"]
        assert corrected.status == "draft" and corrected.publisher_acceptance_id is None
        assert listing.revisions.count() == revision_count + 1
        assert listing.status == "paused"
        assert listing.lifecycle_version == before_listing[1] + 1
        assert listing.approved_revision_id == original_revision.pk
    else:
        assert result.corrected_revision_id is None
        assert listing.revisions.count() == revision_count
        assert (
            listing.status,
            listing.lifecycle_version,
            listing.available_until,
        ) == before_listing


@pytest.mark.parametrize("mutation", ["account", "proof"])
def test_confirmation_rechecks_authority_after_observed_account_lock(
    request, settings, monkeypatch, mutation
):
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue

    from django.core.exceptions import ValidationError
    from django.db import connection, connections, transaction
    from test_photo_reuse_races import observe_blocked

    from apps.core.models import User
    from apps.safety.account_email_confirmation import inspect_token

    case, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    raw = urlsplit(unseal(token.encrypted_delivery)["url"]).path.rstrip("/").split("/")[-1]
    pids = Queue()

    def confirming():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                inspect_token(token.pk, raw, confirm=True)
            except ValidationError:
                return "denied"
            return "confirmed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=person.subject_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(confirming)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if mutation == "account":
                user.first_name = "Synthetic changed while confirmation waits"
                user.save(update_fields=["first_name"])
            else:
                type(token.proof).objects.filter(pk=token.proof_id).update(status="pending")
        assert future.result(timeout=10) == "denied"
    token.refresh_from_db()
    person.subject.refresh_from_db()
    assert token.confirmed_at is None and token.consumed_at is None
    assert person.subject.email != "new-subject@example.invalid"
    assert token.encrypted_delivery
