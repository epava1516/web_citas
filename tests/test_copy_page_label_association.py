"""Two native copy forms retain separate label targets without changing POST names."""

import json
import shutil
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsCopyPageReview
from apps.safety.rights_exports import PageReviewForm

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic / literal scoped page review reason"


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_native_page_labels_error_save_and_replay(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    if account_only:
        case, _, staff, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, _, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)
    with translation.override(language):
        path = reverse("rights_export_prepare", args=[case.pk])
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
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
            page.locator("#id_operation").select_option("inspect_page")
            page.locator("#id_section").select_option("subject_account")
            page.locator("#id_purpose").fill("Inspect synthetic scoped account page before review")
            with page.expect_response(lambda r: r.request.method == "POST") as inspected:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert inspected.value.status == 200
            review = page.locator("form").filter(
                has=page.get_by_role(
                    "button",
                    name="Save page decisions"
                    if language == "en"
                    else "Guardar decisiones de página",
                    exact=True,
                )
            )
            reason_label = review.locator("label").filter(
                has_text="Private review reason:"
                if language == "en"
                else "Motivo privado de revisión:"
            )
            reason_label.click()
            expect(review.locator('[name="reason"]')).to_be_focused()
            ids = page.locator("[id]").evaluate_all("(nodes)=>nodes.map(n=>n.id)")
            assert len(ids) == len(set(ids))
            control = review.locator('[name="reason"]')
            assert reason_label.get_attribute("for") == control.get_attribute("id")
            page.keyboard.press("Tab")
            expect(review.locator('[name="entries"]')).to_be_focused()
            entries = json.loads(review.locator('[name="entries"]').input_value())
            original = {
                name: review.locator(f'[name="{name}"]').input_value()
                for name in ["key", "version", "operation", "read_id", "page_version", "entries"]
            }
            assert set(original) == {
                "key",
                "version",
                "operation",
                "read_id",
                "page_version",
                "entries",
            }
            review.evaluate("f=>f.noValidate=true")
            control.fill("short")
            review.get_by_role("button").focus()
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.keyboard.press("Enter")
            assert invalid.value.status == 400
            expect(page.locator(".errorlist").first).to_be_focused()
            expect(page.locator('[name="reason"]')).to_have_attribute("aria-invalid", "true")
            error_id = page.locator('[name="reason"]').get_attribute("aria-describedby")
            assert error_id and page.locator('[id="' + error_id.split()[0] + '"]').count() == 1
            label = page.locator("label").filter(
                has_text="Private review reason:"
                if language == "en"
                else "Motivo privado de revisión:"
            )
            label.click()
            expect(page.locator('[name="reason"]')).to_be_focused()
            assert db_sync(lambda: RightsCopyPageReview.objects.filter(request=case).count()) == 0
            for name, value in original.items():
                assert page.locator(f'[name="{name}"]').input_value() == value
            page.locator('[name="reason"]').fill(REASON)
            payload = original | {
                "reason": REASON,
                "csrfmiddlewaretoken": page.locator(
                    '[name="csrfmiddlewaretoken"]'
                ).first.input_value(),
            }
            with page.expect_response(lambda r: r.request.method == "POST") as saved:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert saved.value.status == 200
            replay = context.request.post(live_server.url + path, form=payload)
            assert replay.status == 200 and "no-store" in replay.headers["cache-control"]
            assert db_sync(lambda: RightsCopyPageReview.objects.filter(request=case).count()) == 1
            page.goto(live_server.url + path)
            page.reload()
            assert REASON not in page.content() and page.locator('[name="entries"]').count() == 0
        finally:
            browser.close()
    row = RightsCopyPageReview.objects.get(request=case)
    assert (
        unseal(row.encrypted_entries) == entries
        and unseal(row.action.encrypted_reason)["reason"] == REASON
    )
    assert row.section == "subject_account" and row.page == 1 and row.version == 1
    assert RightsAction.objects.filter(request=case, operation="copy_page_save").count() == 1
    assert RightsAction.objects.filter(request=case, operation="copy_page_read").count() == 1
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_auto_id_changes_only_html_identifiers(language):
    values = {
        "key": str(uuid4()),
        "version": 1,
        "operation": "save_page",
        "read_id": 1,
        "page_version": 0,
        "reason": REASON,
        "entries": json.dumps([{"literal": "Synthetic / raw"}]),
    }
    with CaptureQueriesContext(connection) as queries:
        legacy = PageReviewForm(values, language=language)
        presented = PageReviewForm(values, language=language, auto_id="page_review_%s")
    assert len(queries) == 0 and legacy.prefix is None and presented.prefix is None
    assert (
        legacy.is_valid() and presented.is_valid() and legacy.cleaned_data == presented.cleaned_data
    )
    for name in legacy.fields:
        assert legacy[name].html_name == presented[name].html_name == name
        assert (
            legacy[name].id_for_label == "id_" + name
            and presented[name].id_for_label == "page_review_" + name
        )
    assert legacy.fields["reason"].max_length == presented.fields["reason"].max_length == 2000
