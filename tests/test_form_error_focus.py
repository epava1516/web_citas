"""Real keyboard submission retains error context, field association and private data."""

import json
import shutil

import pytest
from django.core.management import call_command
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.safety.models import RightsAction, RightsExport

pytestmark = pytest.mark.django_db(transaction=True)
RAW = "Synthetic / private compilation reason"


def browser(pw):
    return pw.chromium.launch(
        executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
    )


def check_error_focus(page, next_control):
    error = page.locator("main form .errorlist").first
    expect(error).to_be_focused()
    expect(error).to_be_visible()
    assert error.evaluate("(e)=>getComputedStyle(e).outlineStyle") != "none"
    observed = page.evaluate(
        "({tag:document.activeElement.tagName,id:document.activeElement.id,text:document.activeElement.textContent.slice(0,160)})"
    )
    page.keyboard.press("Tab")
    expect(page.locator(next_control)).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    return observed


@pytest.mark.parametrize("language", ["es", "en"])
def test_public_field_and_nonfield_error_focus(live_server, language, record_property):
    call_command("bootstrap")
    measurements = []
    with sync_playwright() as pw:
        b = browser(pw)
        try:
            for width, height in [(320, 800), (390, 844), (1280, 900)]:
                context = b.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                path = live_server.url + f"/{language}/account/login/"
                assert page.goto(path).status == 200
                assert page.evaluate("document.activeElement===document.body")
                page.locator("form").evaluate("f=>f.noValidate=true")
                button = page.get_by_role(
                    "button", name="Continue" if language == "en" else "Continuar", exact=True
                )
                button.focus()
                with page.expect_response(lambda r: r.request.method == "POST") as denied:
                    page.keyboard.press("Enter")
                assert denied.value.status == 400
                measurements.append({**check_error_focus(page, "#id_email"), "language": language, "viewport": [width, height]})
                email = page.locator("#id_email")
                expect(email).to_have_attribute("aria-invalid", "true")
                description = email.get_attribute("aria-describedby")
                assert (
                    description
                    and page.locator('[id="' + description.split()[0] + '"]').count() == 1
                )
                email.fill("unknown-synthetic@example.invalid")
                page.locator("#id_password").fill("Synthetic-not-a-real-password!719")
                button.focus()
                with page.expect_response(lambda r: r.request.method == "POST") as rejected:
                    page.keyboard.press("Enter")
                assert rejected.value.status == 400
                assert "script-src 'self'" in rejected.value.headers["content-security-policy"]
                measurements.append({**check_error_focus(page, "#id_email"), "language": language, "viewport": [width, height]})
                expect(page.locator("#id_password")).to_have_value("")
                assert "Synthetic-not-a-real-password!719" not in page.content()
                page.goto(path)
                page.reload()
                assert page.evaluate("document.activeElement===document.body")
                page.keyboard.press("Tab")
                expect(page.locator(".skip")).to_be_focused()
                context.close()
        finally:
            b.close()
    record_property("error_focus_observed", json.dumps(measurements))


@pytest.mark.parametrize("language", ["es", "en"])
def test_private_native_conflict_focus(request, settings, live_server, language, record_property):
    settings.DEBUG = True
    case, _, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)

    def counts():
        return [
            RightsAction.objects.filter(request=case).count(),
            RightsExport.objects.filter(action__request=case).count(),
        ]

    original = counts()
    measurements = []
    with sync_playwright() as pw:
        b = browser(pw)
        try:
            for width, height in [(320, 800), (390, 844), (1280, 900)]:
                context = b.new_context(viewport={"width": width, "height": height})
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
                path = live_server.url + f"/{language}/moderation/rights/{case.pk}/export/"
                assert page.goto(path).status == 200
                page.locator("#id_operation").select_option("compile_pages")
                page.locator("#id_reason").fill(RAW)
                button = page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                )
                button.focus()
                with page.expect_response(lambda r: r.request.method == "POST") as rejected:
                    page.keyboard.press("Enter")
                assert (
                    rejected.value.status == 409
                    and "no-store" in rejected.value.headers["cache-control"]
                )
                measurements.append({**check_error_focus(page, "#id_operation"), "language": language, "viewport": [width, height]})
                assert page.locator("#id_reason").input_value() == RAW
                assert db_sync(counts) == original
                page.goto(path)
                page.reload()
                assert RAW not in page.content() and page.evaluate(
                    "document.activeElement===document.body"
                )
                context.close()
        finally:
            b.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
    record_property("error_focus_observed", json.dumps(measurements))
