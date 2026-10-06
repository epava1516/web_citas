"""Outcome checks on actual scoped PostgreSQL erasure, not mocked executions."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from test_erasure_execution import PURPOSES, REASON, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken
from apps.safety.crypto import seal, unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_final import snapshot
from apps.safety.models import RecoveryOutbox
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def material(case, execution):
    with transaction.atomic():
        current, person, listing = locked_case(
            case.pk, lock_listing=True, allow_erased_account=True
        )
        return snapshot(current, person, listing, execution.pk)


def test_final_material_preserves_pending_and_detects_reintroduced_credentials(
    request, settings, monkeypatch
):
    case, user, _, _, _, person, plan, _, _, outsider = plan_fixture(request, settings, monkeypatch)
    original_token = AccountToken.objects.filter(user=person.subject).get()
    execution = execute(user, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    person.refresh_from_db()
    result = material(case, execution)
    assert result["completed_purposes"] == sorted(PURPOSES)
    assert not result["pending_execution_purposes"]
    assert result["remaining_decisions"] and result["operational_pending"]
    assert result["identity_simulated"] is True and case.status == "reviewing"
    AccountToken.objects.create(
        user=outsider,
        purpose="reset",
        digest="1" * 64,
        expires_at=timezone.now() + timezone.timedelta(hours=1),
    )
    assert material(case, execution) == result
    AccountToken.objects.create(
        pk=original_token.pk,
        user=person.subject,
        purpose="reset",
        digest=original_token.digest,
        expires_at=original_token.expires_at,
    )
    observed = material(case, execution)
    assert observed["pending_execution_purposes"] == ["authentication"]
    assert "authentication" not in observed["completed_purposes"]


def test_final_material_rejects_foreign_receipt_and_modified_plan(request, settings, monkeypatch):
    case, user, _, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(user, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    before = material(case, execution)
    outbox = RecoveryOutbox.objects.get(execution=execution)
    original = outbox.encrypted_event
    receipt = unseal(original)
    receipt["subject"] = str(uuid4())
    outbox.encrypted_event = seal(receipt)
    outbox.save(update_fields=["encrypted_event"])
    with pytest.raises(ValidationError, match="receipt or scope"):
        material(case, execution)
    outbox.encrypted_event = original
    outbox.save(update_fields=["encrypted_event"])
    decisions = unseal(plan.encrypted_decisions)
    decisions["decisions"][0]["reason"] = (
        "Changed after execution without the signed planning decision"
    )
    plan.encrypted_decisions = seal(decisions)
    plan.save(update_fields=["encrypted_decisions"])
    with pytest.raises(ValidationError, match="receipt or scope"):
        material(case, execution)
    case.refresh_from_db()
    assert case.status == "reviewing" and before["operational_pending"]


def test_final_draft_requires_independent_read_and_current_execution(
    request, settings, monkeypatch
):
    from django.contrib.auth.models import Permission
    from django.core.exceptions import PermissionDenied
    from django.test import Client
    from test_rights_verification import read as read_case

    from apps.core.models import User
    from apps.safety.erasure_final import inspect, prepare, review
    from apps.safety.models import RightsAction

    case, user, staff, _, _, person, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    token = AccountToken.objects.get(user=person.subject)
    execution = execute(user, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
    draft = prepare(
        user,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        uuid4(),
        REASON,
        "Se han suprimido las credenciales y preferencias indicadas; quedan finalidades pendientes de revisión.",
        True,
    )
    assert "credenciales" not in draft.encrypted_reason
    with pytest.raises(PermissionDenied):
        inspect(
            user,
            case.pk,
            case.version,
            case.response_version,
            draft.pk,
            "Inspect final erasure response independently",
        )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.mfa_enabled = True
    reviewer.mfa_version = 1
    reviewer.save(update_fields=["mfa_enabled", "mfa_version"])
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "respond_rights_request",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    audit, body = inspect(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        "Inspect final erasure response independently",
    )
    assert body["material"]["operational_pending"]
    key = uuid4()
    accepted = review(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        audit.pk,
        key,
        "approved",
        REASON,
    )
    assert (
        review(
            reviewer,
            case.pk,
            case.version,
            case.response_version,
            draft.pk,
            audit.pk,
            key,
            "approved",
            REASON,
        ).pk
        == accepted.pk
    )
    assert RightsAction.objects.filter(operation="erase_final_review").count() == 1
    AccountToken.objects.create(
        pk=token.pk,
        user=person.subject,
        purpose=token.purpose,
        digest=token.digest,
        expires_at=token.expires_at,
    )
    with pytest.raises(ValidationError, match="execution changed"):
        review(
            reviewer,
            case.pk,
            case.version,
            case.response_version,
            draft.pk,
            audit.pk,
            uuid4(),
            "approved",
            REASON,
        )
    case.refresh_from_db()
    assert case.status == "reviewing" and not case.responses.exists()


@pytest.mark.parametrize("race", [False, True])
def test_final_http_issues_partial_response_once_with_private_receipt(
    request, settings, monkeypatch, race
):
    from django.contrib.auth.models import Permission
    from django.test import Client
    from test_rights_verification import read as read_case

    from apps.core.models import User
    from apps.safety.erasure_final import inspect, issue, review
    from apps.safety.models import RightsAction, RightsNotice, RightsResponse

    case, user, staff, client, receipt, _, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch
    )
    execution = execute(user, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
    version, responses = case.version, case.response_version
    path = f"/en/moderation/rights/{case.pk}/erasure/final/"
    text = "We have erased the credentials and preferences listed. Other purposes and operational checks remain pending."
    assert staff.get(path).status_code == 200
    assert (
        staff.post(
            path,
            {
                "operation": "prepare",
                "key": uuid4(),
                "version": version,
                "responses": responses,
                "execution": execution.pk,
                "reason": REASON,
                "text": text,
                "confirmed": True,
            },
        ).status_code
        == 302
    )
    draft = RightsAction.objects.get(operation="erase_final_draft")
    assert text.encode() not in staff.get(path).content
    assert client.get(path).status_code in {302, 403}
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.mfa_enabled = True
    reviewer.mfa_version = 1
    reviewer.save(update_fields=["mfa_enabled", "mfa_version"])
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "respond_rights_request",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    audited, _ = inspect(
        reviewer,
        case.pk,
        version,
        responses,
        draft.pk,
        "Inspect exact erasure response before issuance",
    )
    approved = review(
        reviewer, case.pk, version, responses, draft.pk, audited.pk, uuid4(), "approved", REASON
    )
    key = uuid4()
    payload = {
        "operation": "issue",
        "key": key,
        "version": version,
        "responses": responses,
        "review": approved.pk,
    }
    if race:
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        from django.db import close_old_connections, connections

        barrier = Barrier(2)

        def concurrent_issue():
            close_old_connections()
            try:
                current_actor = User.objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                return issue(current_actor, case.pk, version, responses, approved.pk, key).pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(concurrent_issue) for _ in range(2)]
            assert futures[0].result(timeout=30) == futures[1].result(timeout=30)
    else:
        assert staff.post(path, payload).status_code == 302
    assert staff.post(path, payload).status_code == 302
    result = RightsResponse.objects.get(key=key)
    assert (
        result.kind == "erase_partial" and RightsNotice.objects.filter(response=result).count() == 1
    )
    body = unseal(result.encrypted_response)
    assert not body["erasure"]["complete"] and body["erasure"]["operational_pending"]
    assert all(
        set(row) == {"purpose", "operation", "review_on"}
        for row in body["erasure"]["remaining_decisions"]
    )
    assert REASON not in result.encrypted_response
    case.refresh_from_db()
    assert (
        case.status == "reviewing"
        and case.version == version + 1
        and case.response_version == responses + 1
    )
    page = client.get(receipt)
    assert page.status_code == 200 and text.encode() in page.content
    assert b"Partial response" in page.content and REASON.encode() not in page.content
    with pytest.raises(ValidationError):
        issue(user, case.pk, version, responses, approved.pk, uuid4())
    assert RightsResponse.objects.filter(request=case).count() == 1
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    session = csrf.session
    session["mfa_version"] = user.mfa_version
    session.save()
    assert csrf.post(path, payload).status_code == 403


@pytest.mark.parametrize("agency", [False, True])
def test_final_account_erasure_uses_original_proof_after_execution(
    request, settings, monkeypatch, agency
):
    from django.contrib.auth.models import Permission
    from django.test import Client
    from test_account_erasure_execution import prepared_erasure
    from test_rights_verification import read as read_case

    from apps.core.models import Agency, Person, User
    from apps.safety.erasure_final import inspect, issue, prepare, review

    case, actor, staff, subject, public, receipt, plan, purposes, _, _ = prepared_erasure(
        request, settings, monkeypatch, agency
    )
    profiles, organizations = (
        list(Person.objects.order_by("pk").values()),
        list(Agency.objects.order_by("pk").values()),
    )
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    case.refresh_from_db()
    subject.refresh_from_db()
    assert case.person_id is None and subject.is_active is agency
    read_case(staff, case)
    draft = prepare(
        actor,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        uuid4(),
        REASON,
        "Se ha ejecutado la supresión de datos propios indicada. Las finalidades conservadas y las comprobaciones pendientes requieren seguimiento.",
        True,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.mfa_enabled = True
    reviewer.mfa_version = 1
    reviewer.save(update_fields=["mfa_enabled", "mfa_version"])
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "respond_rights_request",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    audit, body = inspect(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        "Inspect account erasure without linking another subject",
    )
    assert body["material"]["completed_purposes"] == sorted(purposes)
    accepted = review(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        audit.pk,
        uuid4(),
        "approved",
        REASON,
    )
    key, version, responses = uuid4(), case.version, case.response_version
    response = issue(actor, case.pk, version, responses, accepted.pk, key)
    assert issue(actor, case.pk, version, responses, accepted.pk, key).pk == response.pk
    assert response.kind == "erase_partial"
    assert public.get(receipt).status_code == 200
    assert profiles == list(Person.objects.order_by("pk").values())
    assert organizations == list(Agency.objects.order_by("pk").values())
    case.refresh_from_db()
    assert case.status == "reviewing"


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_erasure_response_review_issue_and_acknowledgement(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    import json
    import shutil
    from concurrent.futures import ThreadPoolExecutor

    import pyotp
    from django.contrib.auth.models import Permission
    from django.db import close_old_connections
    from playwright.sync_api import expect, sync_playwright

    from apps.core.mfa import encrypt
    from apps.core.models import User
    from apps.safety.models import RightsAction, RightsResponse, RightsResponseAcknowledgement

    settings.DEBUG = True
    case, actor, _, _, receipt, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.mfa_enabled = True
    reviewer.mfa_version = 1
    reviewer.save(update_fields=["mfa_enabled", "mfa_version"])
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "respond_rights_request",
            ]
        )
    )
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.save(update_fields=["mfa_secret_encrypted"])
    credentials["accounts"]["visitor"]["totp_secret"] = secret
    path = f"/{language}/moderation/rights/{case.pk}/erasure/final/"
    text = "Se han borrado las credenciales y preferencias comprobadas. Continúan pendientes las demás finalidades y las comprobaciones operativas."

    def database(operation):
        def perform():
            close_old_connections()
            try:
                return operation()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(perform).result(timeout=30)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:

            def login(name):
                page = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
                account = credentials["accounts"][name]
                page.goto(live_server.url + f"/{language}/account/login/")
                page.locator("[name=email]").fill(account["email"])
                page.locator("[name=password]").fill(credentials["password"])
                page.locator("button[type=submit]").click()
                page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
                page.locator("button[type=submit]").click()
                page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
                page.locator("[name=purpose]").fill(
                    "Read current erasure case and outgoing response history"
                )
                page.locator("button[type=submit]").first.click()
                page.goto(live_server.url + path)
                return page

            author_page = login("moderator")
            author_page.locator("[name=operation]").select_option("prepare")
            author_page.locator("[name=execution]").fill(str(execution.pk))
            author_page.locator("[name=reason]").fill(REASON)
            author_page.locator("[name=text]").fill(text)
            author_page.locator("[name=confirmed]").check()
            author_page.locator("button[type=submit]").click()
            draft = database(
                lambda: RightsAction.objects.get(request=case, operation="erase_final_draft")
            )
            expect(author_page.locator("body")).not_to_contain_text(text)
            other = login("visitor")
            other.locator("[name=operation]").select_option("inspect")
            other.locator("[name=draft]").fill(str(draft.pk))
            other.locator("[name=purpose]").fill(
                "Inspect exact response and pending erasure decisions"
            )
            other.locator("button[type=submit]").click()
            expect(other.locator("body")).to_contain_text(text)
            other.locator("[name=reason]").fill(REASON)
            other.locator("button[type=submit]").click()
            approval = database(
                lambda: RightsAction.objects.get(request=case, operation="erase_final_review")
            )
            author_page.goto(live_server.url + path)
            author_page.locator("[name=operation]").select_option("issue")
            author_page.locator("[name=review]").fill(str(approval.pk))
            author_page.locator("button[type=submit]").click()
            response = database(lambda: RightsResponse.objects.get(request=case))
            assert response.kind == "erase_partial"
            receipt_page = browser.new_page(viewport={"width": 390, "height": 844})
            receipt_page.goto(live_server.url + receipt.replace("/en/", f"/{language}/", 1))
            expect(receipt_page.locator("body")).to_contain_text(text)
            expect(receipt_page.locator("body")).not_to_contain_text(REASON)
            for page in [author_page, other, receipt_page]:
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            receipt_page.locator("[name=received]").check()
            receipt_page.locator('form[action*="acknowledge"] button').click()
            assert database(
                lambda: RightsResponseAcknowledgement.objects.filter(response=response).exists()
            )
            database(case.refresh_from_db)
            assert case.status == "reviewing"
        finally:
            browser.close()


def test_final_media_requires_actual_file_absence_even_after_completed_job(
    request, settings, monkeypatch
):
    from apps.mediafiles.erasure import erase_due_media
    from apps.mediafiles.models import Blob, MediaErasure

    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=["media"]
    )
    blob = person.listing.approved_revision.photos.first().blob
    paths = {field: getattr(blob, field).name for field in ["original", "derivative"]}
    assert all(Blob._meta.get_field(field).storage.exists(path) for field, path in paths.items())
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, ["media"], REASON, True)
    case.refresh_from_db()
    assert material(case, execution)["pending_execution_purposes"] == ["media"]
    assert erase_due_media() >= 1
    result = material(case, execution)
    assert result["completed_purposes"] == ["media"] and not result["pending_execution_purposes"]
    job = MediaErasure.objects.get(blob=blob)
    assert job.status == "completed" and not job.encrypted_paths
    storage = Blob._meta.get_field("original").storage
    with storage.open(paths["original"], "wb") as stream:
        stream.write(b"synthetic reintroduced file")
    try:
        observed = material(case, execution)
        assert observed["pending_execution_purposes"] == ["media"]
        assert not observed["completed_purposes"]
    finally:
        storage.delete(paths["original"])
    assert material(case, execution) == result
    assert result["operational_pending"] and result["remaining_decisions"]
