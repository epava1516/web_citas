"""Final-response material must describe actual scoped processing effects."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from test_processing_execution import prepared
from test_processing_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import seal, unseal
from apps.safety.models import PurposeRestriction
from apps.safety.processing_execution import execute
from apps.safety.processing_final import snapshot
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def material(case, execution):
    with transaction.atomic():
        current, person, listing = locked_case(
            case.pk, lock_listing=True, allow_erased_account=True
        )
        return snapshot(current, person, listing, execution.pk)


@pytest.mark.parametrize("kind", ["restriction", "object"])
def test_processing_response_material_preserves_kind_and_detects_lifted_effect(
    request, settings, monkeypatch, kind
):
    import test_processing_review

    original = test_processing_review.prepared_account
    monkeypatch.setattr(
        test_processing_review,
        "prepared_account",
        lambda request, settings, monkeypatch, _: original(request, settings, monkeypatch, kind),
    )
    case, actor, subject, plan, favorite, _ = prepared(request, settings, monkeypatch)
    execution = execute(
        actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
    )
    case.refresh_from_db()
    body = material(case, execution)
    assert body["kind"] == kind and body["data_deleted"] is False
    assert not body["pending_purposes"] and body["operational_pending"]
    outcomes = {row["purpose"]: row["state"] for row in body["decisions"]}
    assert outcomes["account_preferences"] == "restricted"
    assert "continued_with_reviewed_grounds" in set(outcomes.values())
    assert case.status == "reviewing" and subject.is_active and favorite.pk
    restriction = PurposeRestriction.objects.get(execution=execution)
    restriction.active = False
    restriction.save(update_fields=["active"])
    assert material(case, execution)["pending_purposes"] == ["account_preferences"]
    restriction.active = True
    restriction.save(update_fields=["active"])
    assert material(case, execution) == body
    result = unseal(execution.encrypted_result)
    result["blocked"] = ["publication"]
    execution.encrypted_result = seal(result)
    execution.save(update_fields=["encrypted_result"])
    with pytest.raises(ValidationError, match="result changed"):
        material(case, execution)


@pytest.mark.parametrize("kind", ["restriction", "object"])
def test_processing_response_http_requires_exact_independent_review_and_keeps_pending(
    request, settings, monkeypatch, kind
):
    import test_processing_review
    from django.contrib.auth.models import Permission
    from django.test import Client
    from test_rights_verification import read

    from apps.safety.models import RightsAction, RightsNotice, RightsResponse

    original = test_processing_review.prepared_account
    channel = {}

    def prepared_kind(request, settings, monkeypatch, _):
        result = original(request, settings, monkeypatch, kind)
        channel["receipt"] = result[-1]
        return result

    monkeypatch.setattr(test_processing_review, "prepared_account", prepared_kind)
    case, actor, subject, plan, favorite, other = prepared(request, settings, monkeypatch)
    execution = execute(
        actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
    )
    case.refresh_from_db()
    reviewer = plan.processingplanreview.action.actor
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    staff = Client()
    staff.force_login(actor)
    session = staff.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    read(staff, case)
    read(other, case)
    path = f"/en/moderation/rights/{case.pk}/processing/final/"
    text = "The requested purpose is restricted. Other processing continues on reviewed grounds. Operational checks remain pending."
    common = {"version": case.version, "responses": case.response_version}
    assert staff.get(path).status_code == 200
    assert (
        staff.post(
            path,
            common
            | {
                "key": uuid4(),
                "operation": "prepare",
                "execution": execution.pk,
                "reason": REASON,
                "text": text,
                "confirmed": True,
            },
        ).status_code
        == 302
    )
    draft = RightsAction.objects.get(request=case, operation="process_final_draft")
    assert text.encode() not in staff.get(path).content
    assert (
        staff.post(
            path,
            common
            | {
                "key": uuid4(),
                "operation": "inspect",
                "draft": draft.pk,
                "purpose": "Inspect exact final response independently",
            },
        ).status_code
        == 403
    )
    inspected = other.post(
        path,
        common
        | {
            "key": uuid4(),
            "operation": "inspect",
            "draft": draft.pk,
            "purpose": "Inspect exact final response independently",
        },
    )
    assert inspected.status_code == 200 and text.encode() in inspected.content
    audit = RightsAction.objects.get(request=case, operation="process_final_read")
    assert (
        other.post(
            path,
            common
            | {
                "key": uuid4(),
                "operation": "review",
                "draft": draft.pk,
                "read": audit.pk,
                "outcome": "approved",
                "reason": REASON,
            },
        ).status_code
        == 302
    )
    approval = RightsAction.objects.get(request=case, operation="process_final_review")
    issue_payload = common | {"key": uuid4(), "operation": "issue", "review": approval.pk}
    restriction = PurposeRestriction.objects.get(execution=execution)
    PurposeRestriction.objects.filter(pk=restriction.pk).update(active=False)
    assert staff.post(path, issue_payload).status_code == 409
    assert not RightsResponse.objects.filter(request=case).exists()
    PurposeRestriction.objects.filter(pk=restriction.pk).update(active=True)
    assert staff.post(path, issue_payload).status_code == 302
    assert staff.post(path, issue_payload).status_code == 302
    response = RightsResponse.objects.get(request=case)
    assert (
        response.kind == kind + "_partial"
        and RightsNotice.objects.filter(response=response).count() == 1
    )
    result = unseal(response.encrypted_response)["processing"]
    assert result["kind"] == kind and result["data_deleted"] is False and not result["complete"]
    assert all(
        set(row) == {"purpose", "operation", "state", "review_on"} for row in result["decisions"]
    )
    receipt = Client().get(channel["receipt"])
    assert receipt.status_code == 200 and text.encode() in receipt.content
    assert REASON.encode() not in receipt.content
    assert (b"Objection result" if kind == "object" else b"Restriction result") in receipt.content
    case.refresh_from_db()
    subject.refresh_from_db()
    favorite.refresh_from_db()
    assert case.status == "reviewing" and subject.is_active and favorite.pk


@pytest.mark.parametrize(
    "kind,mode,mixed", [("restriction", "restrict", False), ("object", "cease", True)]
)
def test_processing_profile_response_checks_publication_and_current_review_calendar(
    request, settings, monkeypatch, kind, mode, mixed
):
    from datetime import timedelta

    from django.contrib.auth.models import Permission
    from django.test import Client
    from django.utils import timezone
    from test_rights_responses import ready
    from test_rights_verification import read

    from apps.core.models import User
    from apps.listings.models import Favorite
    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.processing_final import (
        inspect,
        issue,
    )
    from apps.safety.processing_final import (
        prepare as response_draft,
    )
    from apps.safety.processing_final import (
        review as response_review,
    )
    from apps.safety.processing_plans import prepare as plan_draft
    from apps.safety.processing_review import record

    case, actor, staff, public, receipt, person = ready(request, settings, monkeypatch, kind)
    if mixed:
        Favorite.objects.create(user=person.subject, listing=person.listing)
    selected = ["publication", "account_preferences"] if mixed else ["publication"]
    with transaction.atomic():
        manifest = source_manifest(person, case)
    decisions = [
        dict(
            purpose=purpose,
            operation=mode if purpose in selected else "continue",
            basis=REASON,
            reason=REASON,
            scope=REASON,
            review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for purpose in sorted({row["purpose"] for row in manifest["entries"]})
    ]
    plan = plan_draft(actor, case.pk, uuid4(), case.version, REASON, decisions)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_processing_plan",
                "respond_rights_request",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(other, case)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    revisions = list(person.listing.revisions.order_by("pk").values())
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, selected, REASON, True)
    case.refresh_from_db()
    read(staff, case)
    read(other, case)
    before = material(case, execution)
    assert not before["pending_purposes"]
    expected = "restricted" if mode == "restrict" else "ceased"
    assert all(
        row["state"] == expected for row in before["decisions"] if row["purpose"] in selected
    )
    text = "Se ha detenido el tratamiento de publicación indicado. Los datos se conservan y las comprobaciones operativas siguen pendientes."
    draft = response_draft(
        actor,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        uuid4(),
        REASON,
        text,
        True,
    )
    audited, _ = inspect(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        "Inspect exact publication response and review dates",
    )
    approval = response_review(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        draft.pk,
        audited.pk,
        uuid4(),
        "approved",
        REASON,
    )
    hold = execution.publication_hold
    original_date = hold.purpose_review_on
    hold.purpose_review_on += timedelta(days=1)
    hold.version += 1
    hold.save(update_fields=["purpose_review_on", "version"])
    with pytest.raises(ValidationError, match="changed or expired"):
        issue(actor, case.pk, case.version, case.response_version, approval.pk, uuid4())
    current = material(case, execution)
    publication = next(row for row in current["decisions"] if row["purpose"] == "publication")
    assert publication["review_on"] == hold.purpose_review_on.isoformat()
    assert publication["initial_review_on"] == original_date.isoformat()
    hold.active = False
    hold.save(update_fields=["active"])
    assert "publication" in material(case, execution)["pending_purposes"]
    assert revisions == list(person.listing.revisions.order_by("pk").values())
    assert public.get(receipt).status_code == 200
    case.refresh_from_db()
    assert case.status == "reviewing" and not case.responses.exists()
    hold.active = True
    hold.save(update_fields=["active"])
    renewed = response_draft(
        actor,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        uuid4(),
        REASON,
        text,
        True,
    )
    inspected, _ = inspect(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        renewed.pk,
        "Inspect renewed response with current calendar date",
    )
    approved = response_review(
        reviewer,
        case.pk,
        case.version,
        case.response_version,
        renewed.pk,
        inspected.pk,
        uuid4(),
        "approved",
        REASON,
    )
    response = issue(actor, case.pk, case.version, case.response_version, approved.pk, uuid4())
    projected = unseal(response.encrypted_response)["processing"]
    publication = next(row for row in projected["decisions"] if row["purpose"] == "publication")
    assert publication["review_on"] == hold.purpose_review_on.isoformat()
    assert response.kind == kind + "_partial" and projected["data_deleted"] is False
    assert text.encode() in public.get(receipt).content
    assert revisions == list(person.listing.revisions.order_by("pk").values())


@pytest.mark.parametrize("language,kind", [("es", "restriction"), ("en", "object")])
def test_mobile_processing_response_exact_review_issue_and_receipt(
    live_server, request, settings, monkeypatch, language, kind
):
    import shutil
    from concurrent.futures import ThreadPoolExecutor

    import test_processing_review
    from django.contrib.auth.models import Permission
    from django.db import close_old_connections
    from django.test import Client
    from playwright.sync_api import expect, sync_playwright
    from test_partial_response_localization import assert_form, check_missing_preparation
    from test_rights_verification import read

    from apps.safety.models import RightsAction, RightsResponse, RightsResponseAcknowledgement

    settings.DEBUG = True
    original = test_processing_review.prepared_account
    channel = {}

    def prepared_kind(request, settings, monkeypatch, _):
        result = original(request, settings, monkeypatch, kind)
        channel["receipt"] = result[-1]
        return result

    monkeypatch.setattr(test_processing_review, "prepared_account", prepared_kind)
    case, actor, _, plan, _, reviewer_client = prepared(request, settings, monkeypatch)
    execution = execute(
        actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
    )
    case.refresh_from_db()
    reviewer = plan.processingplanreview.action.actor
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    actor_client = Client()
    actor_client.force_login(actor)
    session = actor_client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    read(actor_client, case)
    read(reviewer_client, case)
    path = f"/{language}/moderation/rights/{case.pk}/processing/final/"
    text = "La finalidad indicada está limitada. Los datos se conservan y las comprobaciones operativas permanecen pendientes."

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

            def page_for(client):
                context = browser.new_context(viewport={"width": 390, "height": 844})
                context.add_cookies(
                    [
                        {
                            "name": settings.SESSION_COOKIE_NAME,
                            "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                            "url": live_server.url,
                        }
                    ]
                )
                page = context.new_page()
                page.goto(live_server.url + path)
                assert_form(page, language, "process")
                return page

            author = page_for(actor_client)
            check_missing_preparation(author, language, "process", database, case)
            author.locator("[name=operation]").select_option("prepare")
            author.locator("[name=execution]").fill(str(execution.pk))
            author.locator("[name=reason]").fill(REASON)
            author.locator("[name=text]").fill(text)
            author.locator("[name=confirmed]").check()
            author.locator("button[type=submit]").click()
            draft = database(
                lambda: RightsAction.objects.get(request=case, operation="process_final_draft")
            )
            expect(author.locator("body")).not_to_contain_text(text)
            assert_form(author, language, "process")
            independent = page_for(reviewer_client)
            independent.locator("[name=operation]").select_option("inspect")
            independent.locator("[name=draft]").fill(str(draft.pk))
            independent.locator("[name=purpose]").fill(
                "Inspect the exact processing response and pending purposes"
            )
            independent.locator("button[type=submit]").click()
            expect(independent.locator("body")).to_contain_text(text)
            assert_form(independent, language, "process")
            independent.locator("[name=reason]").fill(REASON)
            independent.locator("button[type=submit]").click()
            approval = database(
                lambda: RightsAction.objects.get(request=case, operation="process_final_review")
            )
            assert_form(independent, language, "process")
            author.goto(live_server.url + path)
            assert_form(author, language, "process")
            author.locator("[name=operation]").select_option("issue")
            author.locator("[name=review]").fill(str(approval.pk))
            author.locator("button[type=submit]").click()
            assert_form(author, language, "process")
            response = database(lambda: RightsResponse.objects.get(request=case))
            assert response.kind == kind + "_partial"
            receipt = browser.new_page(viewport={"width": 390, "height": 844})
            receipt.goto(live_server.url + channel["receipt"].replace("/en/", f"/{language}/", 1))
            expect(receipt.locator("body")).to_contain_text(text)
            expect(receipt.locator("body")).not_to_contain_text(REASON)
            for page in [author, independent, receipt]:
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            receipt.locator("[name=received]").check()
            receipt.locator('form[action*="acknowledge"] button').click()
            assert database(
                lambda: RightsResponseAcknowledgement.objects.filter(response=response).exists()
            )
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing"
