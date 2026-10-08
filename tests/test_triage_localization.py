"""Localized triage presentation with real PG/TCP and unchanged assignment guards."""

import re
import shutil

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import User
from apps.safety.models import (
    Complaint,
    ComplaintAction,
    Report,
    ReportAction,
    RightsAction,
    RightsRequest,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("family", ["report", "complaint", "rights"])
def test_triage_localization_preserves_assignment_replay_and_authority(
    directory,  # noqa: F811
    live_server,
    language,
    family,
):  # noqa: F811
    assert connection.vendor == "postgresql"
    visitor = Client()
    suffix = {"report": "report/", "complaint": "complaints/", "rights": "rights/"}[family]
    intake = f"/{language}/safety/" + suffix
    submitted = visitor.get(intake).context["form"].initial | {
        "reference": "Synthetic private reference",
        "explanation": "Synthetic confidential intake explanation, not real personal data.",
        "email": "private-triage@example.invalid",
        "name": "Synthetic private claimant",
    }
    submitted |= {
        "report": {"mode": "general", "reason": "other", "good_faith": "on"},
        "complaint": {"relationship": "represented"},
        "rights": {"kind": "access"},
    }[family]
    assert visitor.post(intake, submitted).status_code == 302
    model, actions = {
        "report": (Report, ReportAction),
        "complaint": (Complaint, ComplaintAction),
        "rights": (RightsRequest, RightsAction),
    }[family]
    case = model.objects.get()
    cipher, created = case.encrypted_payload, case.created_at
    user = User.objects.get(username="fixture-v1-moderator")
    user.user_permissions.clear()
    user.groups.clear()
    review_code = {
        "report": "review_report",
        "complaint": "review_complaint",
        "rights": "review_rights_request",
    }[family]
    coord_code = {
        "report": "manage_report_assignment",
        "complaint": "manage_complaint_assignment",
        "rights": "manage_rights_assignment",
    }[family]
    review = Permission.objects.get(codename=review_code)
    user.user_permissions.add(review, Permission.objects.get(codename=coord_code))
    staff = Client()
    staff.force_login(user)
    session = staff.session
    session["mfa_version"] = user.mfa_version
    session.save()
    assert user.mfa_enabled  # Persisted synthetic session fixture, not TOTP enrollment evidence.
    inspect_path = (
        f"/{language}/moderation/"
        + {"report": "reports/", "complaint": "complaints/", "rights": "rights/"}[family]
        + str(case.pk)
        + "/"
    )
    path = inspect_path + ("decision/" if family == "report" else "action/")
    # Choice values remain the authoritative operation IDs, independently of presentation.
    form = staff.get(path).context["form"]
    expected_ids = {
        "report": ["claim", "unassign", "uphold", "lift", "link", "restrict", "dismiss"],
        "complaint": ["claim", "unassign", "link", "link_listing", "clarify", "reassess"],
        "rights": ["claim", "link", "clarify", "withdraw", "extend", "unassign"],
    }[family]
    assert [value for value, _ in form.fields["operation"].choices] == expected_ids
    reason_text = "Review of synthetic private evidence supports assignment only"
    button = {
        "report": ("Registrar acción del caso", "Record case action"),
        "complaint": ("Registrar acción", "Record request action"),
        "rights": ("Registrar acción de asignación", "Record assignment action"),
    }[family][language == "en"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
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
            assert page.goto(live_server.url + path).status == 200
            for field in form.visible_fields():
                expect(
                    page.get_by_label(re.compile("^" + re.escape(field.label) + ":?$"), exact=True)
                ).to_be_visible()
                assert " / " not in field.label
            for name, field in form.fields.items():
                if hasattr(field, "choices"):
                    assert page.locator(f'[name="{name}"] option').evaluate_all(
                        "es => es.map(e=>[e.value,e.textContent])"
                    ) == [list(pair) for pair in field.choices]
            assert submitted["email"] not in page.content()
            page.locator("[name=operation]").select_option("claim")
            page.locator("[name=reason]").fill("short")
            page.locator("form").evaluate("e => e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 400
            assert db_sync(lambda: actions.objects.count()) == 0
            expect(page.locator(".errorlist")).to_be_visible()
            page.locator("[name=reason]").fill(reason_text)
            data = page.locator("form").evaluate("e => Object.fromEntries(new FormData(e))")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 302
            page.wait_for_url(live_server.url + inspect_path)
            assert submitted["email"] not in page.content()
            state = db_sync(lambda: model.objects.get(pk=case.pk))
            assert state.assigned_to_id == user.pk and state.version == case.version + 1
            record = db_sync(lambda: actions.objects.get())
            assert record.actor_id == user.pk and record.operation == "claim"
            assert reason_text not in record.encrypted_reason
            replay = page.request.post(live_server.url + path, form=data, max_redirects=0)
            assert replay.status == 302 and db_sync(lambda: actions.objects.count()) == 1
            stale = data | {"key": str(__import__("uuid").uuid4()), "operation": "unassign"}
            assert page.request.post(live_server.url + path, form=stale).status == 409
            assert db_sync(lambda: actions.objects.count()) == 1
            assert page.goto(live_server.url + path).status == 200
            page.locator("[name=operation]").select_option("unassign")
            page.locator("[name=reason]").fill(reason_text)
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 302
            page.wait_for_url(live_server.url + inspect_path)
            state = db_sync(lambda: model.objects.get(pk=case.pk))
            assert state.assigned_to_id is None and state.version == case.version + 2
            assert state.encrypted_payload == cipher and state.created_at == created
            if family == "rights":
                assert state.initial_due_at == case.initial_due_at and db_sync(
                    lambda: state.effective_due_at == case.effective_due_at
                )
                assert state.scope_status == "unverified"
            assert db_sync(lambda: actions.objects.count()) == 2
            assert page.goto(live_server.url + path).status == 200
            page.reload()
            db_sync(lambda: User.objects.get(pk=user.pk).user_permissions.remove(review))
            assert page.request.post(live_server.url + path, form=data).status == 403
            assert db_sync(lambda: actions.objects.count()) == 2
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
