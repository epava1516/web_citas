"""Actual execution-bound recipient review; synthetic identities, PostgreSQL."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import Client
from test_erasure_execution import PURPOSES, REASON, plan_fixture
from test_processing_execution import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read as read_case

from apps.core.models import User
from apps.safety import rights_communications as communications
from apps.safety.models import RightsAction
from apps.safety.recipient_assessments import targets
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("kind", ["erase", "restriction", "object"])
def test_review_is_independent_exact_audited_and_never_implies_delivery(
    request, settings, monkeypatch, kind
):
    if kind == "erase":
        from apps.safety.erasure_execution import execute

        case, actor, staff, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
        execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    else:
        import test_processing_review

        from apps.safety.processing_execution import execute

        original = test_processing_review.prepared_account
        monkeypatch.setattr(
            test_processing_review,
            "prepared_account",
            lambda request, settings, monkeypatch, _: original(
                request, settings, monkeypatch, kind
            ),
        )
        case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
        execution = execute(
            actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
        )
        staff = Client()
        staff.force_login(actor)
        session = staff.session
        session["mfa_version"] = actor.mfa_version
        session.save()
    case.refresh_from_db()
    read_case(staff, case)
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
                "review_recipient_assessment",
                "review_processing_plan",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    with transaction.atomic():
        current, person, listing = locked_case(
            case.pk, lock_listing=True, allow_erased_account=True
        )
        source = communications.snapshot(current, person, listing, execution.pk)
    assert source["kind"] == kind and source["complete"] is False
    assert not source["manager_notices"] and source["pending"]
    decisions = {
        token: {"outcome": "pending", "reason": REASON, "evidence": REASON}
        for token in targets(source)
    }
    common = (case.pk, case.version, case.response_version)
    with pytest.raises(ValidationError, match="Assess every"):
        communications.propose(
            actor, *common, execution.pk, uuid4(), "Assess incomplete recipient scope", {}
        )
    false_delivery = {
        token: dict(value, outcome="communicated") for token, value in decisions.items()
    }
    with pytest.raises(ValidationError, match="Recorded recipient receipt"):
        communications.propose(
            actor,
            *common,
            execution.pk,
            uuid4(),
            "Assess unsupported recipient delivery",
            false_delivery,
        )
    with pytest.raises(ValidationError, match="Read the current recipient source"):
        communications.propose(
            actor,
            *common,
            execution.pk,
            uuid4(),
            "Assess source without prior audited access",
            decisions,
        )
    source_audit, inspected_source = communications.inspect_source(
        actor, *common, execution.pk, "Inspect current recipients before assessment"
    )
    assert inspected_source == source and source_audit.operation == "rights_comms_source"
    key = uuid4()
    proposal = communications.propose(
        actor, *common, execution.pk, key, "Assess recipients of the executed right", decisions
    )
    assert (
        communications.propose(
            actor, *common, execution.pk, key, "Assess recipients of the executed right", decisions
        ).pk
        == proposal.pk
    )
    with pytest.raises(PermissionDenied):
        communications.inspect(
            actor, *common, proposal.pk, "Attempt independent review of own plan"
        )
    with pytest.raises(ValidationError, match="Exact audited"):
        communications.review(reviewer, *common, proposal.pk, 0, uuid4(), "approved", REASON)
    # Decryption must happen after a transaction-visible audit was recorded.
    original_checked = communications.checked_body

    def checked_after_audit(cipher):
        if cipher == proposal.encrypted_reason:
            assert RightsAction.objects.filter(
                request=case, actor=reviewer, operation="rights_comms_read"
            ).exists()
        return original_checked(cipher)

    monkeypatch.setattr(communications, "checked_body", checked_after_audit)
    audit, body = communications.inspect(
        reviewer, *common, proposal.pk, "Read exact recipient grounds independently"
    )
    assert body["decisions"] == decisions
    review_key = uuid4()
    accepted = communications.review(
        reviewer, *common, proposal.pk, audit.pk, review_key, "approved", REASON
    )
    assert (
        communications.review(
            reviewer, *common, proposal.pk, audit.pk, review_key, "approved", REASON
        ).pk
        == accepted.pk
    )
    assert original_checked(accepted.encrypted_reason)["pending"] is True
    # Even a cached permission must not survive database revocation.
    assert reviewer.has_perm("safety.review_recipient_assessment")
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_recipient_assessment"))
    with pytest.raises(PermissionDenied):
        communications.inspect(
            reviewer, *common, proposal.pk, "Read after revoked review permission"
        )
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == common[1]
    reviewer.user_permissions.add(Permission.objects.get(codename="review_recipient_assessment"))
    path = f"/en/moderation/rights/{case.pk}/communications/"
    assert staff.get(path).status_code == 200
    assert b"Read exact recipient" not in staff.get(path).content
    assert Client(enforce_csrf_checks=True).post(path).status_code == 403
    metadata = {"version": case.version, "responses": case.response_version, "key": uuid4()}
    accessed = staff.post(
        path,
        metadata
        | {
            "operation": "source",
            "execution": execution.pk,
            "purpose": "Read recipients through private structured screen",
        },
    )
    assert accessed.status_code == 200 and accessed.context["decisions"]
    fields = {"decisions-TOTAL_FORMS": len(decisions), "decisions-INITIAL_FORMS": len(decisions)}
    for number, (token, value) in enumerate(decisions.items()):
        fields[f"decisions-{number}-target"] = token
        for field, content in value.items():
            fields[f"decisions-{number}-{field}"] = content
    posted = staff.post(
        path,
        metadata
        | fields
        | {
            "operation": "propose",
            "execution": execution.pk,
            "purpose": "Assess recipients through private structured screen",
        },
    )
    assert posted.status_code == 302
    latest = RightsAction.objects.filter(request=case, operation="rights_comms_plan").latest("pk")
    seen = other.post(
        path,
        metadata
        | {
            "operation": "inspect",
            "plan": latest.pk,
            "purpose": "Read proposed recipient decisions independently",
        },
    )
    assert seen.status_code == 200 and seen.context["inspected"]["decisions"] == decisions
    assert other.get(path).context["inspected"] is None
    recorded = other.post(
        path,
        metadata
        | {
            "operation": "review",
            "key": uuid4(),
            "plan": latest.pk,
            "read": seen.context["form"].initial["read"],
            "outcome": "approved",
            "reason": REASON,
        },
    )
    assert recorded.status_code == 302, recorded.context["form"].errors
    from django.utils import timezone

    from apps.safety.communication_notices import acknowledge, deliver, inspect_notice
    from apps.safety.crypto import unseal
    from apps.safety.models import RightsRecipientNotice

    backend = communications.backend(case.pk)
    approval = RightsAction.objects.filter(request=case, operation="rights_comms_review").latest(
        "pk"
    )
    final_text = "Se ha ejecutado la decisión indicada; quedan comunicaciones y comprobaciones operativas pendientes de completar."
    old_final = backend.prepare(actor, *common, execution.pk, uuid4(), REASON, final_text, True)
    delivery_key = uuid4()
    sent = staff.post(
        path,
        metadata
        | {
            "operation": "deliver",
            "review": approval.pk,
            "key": delivery_key,
        },
    )
    assert sent.status_code == 302, sent.context["form"].errors if sent.context else ""
    delivery = deliver(actor, *common, approval.pk, delivery_key)
    notices = RightsRecipientNotice.objects.filter(request=case)
    assert notices.count() == len(body["source"]["notice_targets"])
    assert delivery.operation == "rights_comms_deliver"
    with pytest.raises(ValidationError, match="changed"):
        backend.inspect(
            reviewer, *common, old_final.pk, "Inspect draft after recipient delivery changed"
        )
    if kind == "erase":
        assert set(notices.values_list("recipient__username", flat=True)) == {
            "fixture-v1-agency",
            "fixture-v1-editor",
        }
    received_accounts = set()
    for index, notice in enumerate(notices.order_by("pk"), 1):
        receiver = User.objects.get(pk=notice.recipient_id)
        receiver.mfa_enabled = True
        receiver.mfa_version = 1
        receiver.save(update_fields=["mfa_enabled", "mfa_version"])
        receiving = Client()
        receiving.force_login(receiver)
        session = receiving.session
        session["mfa_version"] = receiver.mfa_version
        session.save()
        inbox = "/en/account/rights-notices/"
        for foreign_notice in notices.exclude(recipient_id=receiver.pk):
            assert (
                receiving.post(
                    inbox,
                    {
                        "operation": "inspect",
                        "notice": foreign_notice.pk,
                        "purpose": "Attempt another manager's private execution notification",
                    },
                ).status_code
                == 403
            )
        assert receiving.get(inbox).status_code == 200
        assert receiving.get(inbox).context["payload"] is None
        with pytest.raises(ValidationError, match="Read the exact"):
            acknowledge(receiver, notice.pk, 0)
        with pytest.raises(PermissionDenied):
            inspect_notice(reviewer, notice.pk, "Attempt access by another recipient account")
        inspected_notice = receiving.post(
            inbox,
            {
                "operation": "inspect",
                "notice": notice.pk,
                "purpose": "Inspect exact private execution notification",
            },
        )
        assert inspected_notice.status_code == 200
        assert inspected_notice.context["payload"]["kind"] == kind
        assert set(inspected_notice.context["payload"]) == {
            "schema",
            "kind",
            "execution",
            "purposes",
            "simulation",
            "complete",
        }
        notice_read = inspected_notice.context["form"].initial["read"]
        assert (
            receiving.post(
                inbox,
                {
                    "operation": "ack",
                    "notice": notice.pk,
                    "read": notice_read,
                },
            ).status_code
            == 302
        )
        acknowledged = acknowledge(receiver, notice.pk, notice_read)
        assert acknowledged.acknowledged_at and acknowledged.acknowledged_action_id
        assert (
            RightsAction.objects.filter(request=case, operation="rights_notice_ack").count()
            == index
        )
        assert deliver(actor, *common, approval.pk, delivery_key).pk == delivery.pk
        received_accounts.add(str(receiver.pk))
    assert notices.filter(acknowledged_at__isnull=True).count() == 0
    # An unsigned timestamp edit must never become communication evidence.
    timestamp = acknowledged.acknowledged_at
    RightsRecipientNotice.objects.filter(pk=notice.pk).update(
        acknowledged_at=timestamp + timezone.timedelta(seconds=1)
    )
    with pytest.raises(ValidationError, match="receipt audit changed"):
        communications.inspect_source(
            actor, *common, execution.pk, "Inspect modified receipt evidence"
        )
    RightsRecipientNotice.objects.filter(pk=notice.pk).update(acknowledged_at=timestamp)
    _, renewed = communications.inspect_source(
        actor, *common, execution.pk, "Reassess recipients after recorded delivery and receipt"
    )
    renewed_decisions = {
        token: {
            "outcome": "communicated"
            if candidate
            and candidate["kind"] in {"account", "individual"}
            and candidate["reference"] in received_accounts
            else "pending",
            "reason": REASON,
            "evidence": REASON,
        }
        for token, candidate in targets(renewed).items()
    }
    renewed_plan = communications.propose(
        actor,
        *common,
        execution.pk,
        uuid4(),
        "Assess actual internal receipt and remaining gaps",
        renewed_decisions,
    )
    renewed_read, _ = communications.inspect(
        reviewer, *common, renewed_plan.pk, "Read renewed recipient assessment independently"
    )
    communications.review(
        reviewer, *common, renewed_plan.pk, renewed_read.pk, uuid4(), "approved", REASON
    )
    final = backend.prepare(actor, *common, execution.pk, uuid4(), REASON, final_text, True)
    final_read, exact = backend.inspect(
        reviewer, *common, final.pk, "Read exact response and reviewed communication outcome"
    )
    summary = exact["material"]["communications"]
    assert summary["state"] == "reviewed_partial" and summary["acknowledged"] == notices.count()
    assert summary["outcomes"]["communicated"] >= 1 and summary["pending"] is True
    final_review = backend.review(
        reviewer, *common, final.pk, final_read.pk, uuid4(), "approved", REASON
    )
    response_key = uuid4()
    response = backend.issue(actor, *common, final_review.pk, response_key)
    assert backend.issue(actor, *common, final_review.pk, response_key).pk == response.pk
    projected = unseal(response.encrypted_response)["communications"]
    assert set(projected) == {"state", "pending", "outcomes", "delivered", "acknowledged"}
    assert projected["acknowledged"] == notices.count() and projected["pending"] is True
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_same_execution_delivery_serializes_and_old_authority_cannot_read(
    request, settings, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    from apps.safety.communication_notices import deliver, inspect_notice
    from apps.safety.erasure_execution import execute
    from apps.safety.models import RightsRecipientNotice

    case, actor, staff, _, _, person, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
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
                "review_recipient_assessment",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    common = (case.pk, case.version, case.response_version)
    _, source = communications.inspect_source(
        actor, *common, execution.pk, "Read scope for concurrent delivery"
    )
    decisions = {
        token: {"outcome": "pending", "reason": REASON, "evidence": REASON}
        for token in targets(source)
    }
    proposal = communications.propose(
        actor, *common, execution.pk, uuid4(), "Assess scope before concurrent delivery", decisions
    )
    audit, _ = communications.inspect(
        reviewer, *common, proposal.pk, "Read proposed delivery independently"
    )
    approval = communications.review(
        reviewer, *common, proposal.pk, audit.pk, uuid4(), "approved", REASON
    )
    key = uuid4()
    barrier = Barrier(2)

    def deliver_thread():
        close_old_connections()
        try:
            user = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return deliver(user, *common, approval.pk, key).pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: deliver_thread(), range(2)))
    assert results[0] == results[1]
    assert RightsAction.objects.filter(request=case, operation="rights_comms_deliver").count() == 1
    assert RightsRecipientNotice.objects.filter(request=case).count() == len(
        source["notice_targets"]
    )
    notice = RightsRecipientNotice.objects.filter(request=case).first()
    receiver = User.objects.get(pk=notice.recipient_id)
    receiver.mfa_enabled = True
    receiver.mfa_version = 1
    receiver.save(update_fields=["mfa_enabled", "mfa_version"])
    person.refresh_from_db()
    person.manager_version += 1
    person.save(update_fields=["manager_version"])
    before = RightsAction.objects.filter(request=case, operation="rights_notice_read").count()
    with pytest.raises(PermissionDenied):
        inspect_notice(receiver, notice.pk, "Read after manager authorization changed")
    assert (
        RightsAction.objects.filter(request=case, operation="rights_notice_read").count() == before
    )


def test_agency_own_account_notice_does_not_include_owned_models(request, settings, monkeypatch):
    from test_account_erasure_execution import prepared_erasure

    from apps.safety.erasure_execution import execute

    case, actor, staff, subject, _, _, plan, purposes, _, _ = prepared_erasure(
        request, settings, monkeypatch, agency=True
    )
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
    _, source = communications.inspect_source(
        actor,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        "Inspect own agency account without its models",
    )
    assert source["person"] is None and source["account_subject"] == str(subject.pk)
    assert source["notice_targets"] == [
        {"recipient": str(subject.pk), "authorization_version": "account"}
    ]
    assert all(candidate["kind"] == "account" for candidate in source["candidates"])
    assert all(
        evidence["basis"]
        not in {"representation_history", "submission_actor", "publishing_acceptance"}
        for candidate in source["candidates"]
        for evidence in candidate["evidence"]
    )


def test_mobile_recipient_assessment_source_is_audited_in_both_languages(
    live_server, request, settings, monkeypatch
):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    from apps.safety.erasure_execution import execute

    settings.DEBUG = True
    case, actor, staff, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            for language in ["es", "en"]:
                context = browser.new_context(viewport={"width": 390, "height": 844})
                context.add_cookies(
                    [
                        {
                            "name": settings.SESSION_COOKIE_NAME,
                            "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                            "url": live_server.url,
                        }
                    ]
                )
                page = context.new_page()
                path = f"/{language}/moderation/rights/{case.pk}/communications/"
                page.goto(live_server.url + path)
                expect(page.locator("h1")).to_have_text(
                    "Comunicaciones a destinatarios"
                    if language == "es"
                    else "Recipient communications"
                )
                from test_rights_communications_localization import assert_screen

                from apps.safety.communication_notice_views import NoticeForm
                from apps.safety.rights_communication_views import CommunicationForm

                assert_screen(page, language, CommunicationForm)
                assert page.locator("fieldset").count() == 0
                page.locator("[name=operation]").select_option("source")
                page.locator("[name=execution]").fill(str(execution.pk))
                with page.expect_response(
                    lambda response: response.request.method == "POST"
                ) as negative:
                    page.locator("button[type=submit]").click()
                assert negative.value.status == 400
                expect(
                    page.get_by_text("Obligatorio" if language == "es" else "Required", exact=True)
                ).to_be_visible()
                assert_screen(page, language, CommunicationForm)
                assert page.locator("fieldset").count() == 0
                page.locator("[name=purpose]").fill(
                    "Inspect recipients on mobile with audited access"
                )
                page.locator("button[type=submit]").click()
                expect(page.locator("fieldset").first).to_be_visible()
                assert page.locator("fieldset").count() >= 5
                assert_screen(page, language, CommunicationForm)
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.goto(live_server.url + path)
                assert page.locator("fieldset").count() == 0
                page.goto(live_server.url + f"/{language}/account/rights-notices/")
                expect(page.locator("h1")).to_have_text(
                    "Notificaciones privadas sobre derechos"
                    if language == "es"
                    else "Private rights notices"
                )
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                assert_screen(page, language, NoticeForm)
                context.close()
        finally:
            browser.close()
