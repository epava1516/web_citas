"""Bounded CSS viewport reflow over native pages; not a browser zoom test."""

import json
import shutil

import pytest
from django.core.management import call_command
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.safety.models import RightsAction, RightsCopyPageReview, RightsExport

pytestmark = pytest.mark.django_db(transaction=True)
GEOMETRY = """() => {
  const viewport=document.documentElement.clientWidth;
  const observed=[];
  const selector='nav a,main h1,main label,main p,main pre,main .errorlist li,main form input:not([type=hidden]),main form select,main form textarea,main button,footer';
  for (const [index,node] of Array.from(document.querySelectorAll(selector)).entries()) {
    const style=getComputedStyle(node),box=node.getBoundingClientRect();
    if (!node.getClientRects().length || style.visibility==='hidden') continue;
    const range=document.createRange();range.selectNodeContents(node);
    observed.push({index,tag:node.tagName,id:node.id,left:box.left,right:box.right,
      display:style.display,visibility:style.visibility,overflow:style.overflowX,
      lines:Array.from(range.getClientRects()).map(r=>({left:r.left,right:r.right}))});
  }
  return {viewport,inner_width:innerWidth,document_scroll_width:document.documentElement.scrollWidth,
    body_scroll_width:document.body.scrollWidth,observed};
}"""


def snapshot(page, language, state):
    data = page.evaluate(GEOMETRY)
    data.update(
        language=language,
        state=state,
        requested_css_width=page.viewport_size["width"],
        zoom="not_measured",
    )
    assert data["viewport"] == data["inner_width"] == data["requested_css_width"]
    assert (
        data["document_scroll_width"] <= data["viewport"]
        and data["body_scroll_width"] <= data["viewport"]
    ), data
    assert data["observed"]
    for node in data["observed"]:
        assert node["left"] >= -0.5 and node["right"] <= data["viewport"] + 0.5, node
        assert all(
            r["left"] >= -0.5 and r["right"] <= data["viewport"] + 0.5 for r in node["lines"]
        ), node
    return data


@pytest.mark.parametrize("language", ["es", "en"])
def test_public_reflow_and_keyboard_errors(live_server, language, record_property):
    call_command("bootstrap")
    observations = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            for width, height in [(320, 844), (1280, 900)]:
                page = browser.new_page(viewport={"width": width, "height": height})
                path = live_server.url + f"/{language}/account/login/"
                assert page.goto(path).status == 200
                observations.append(snapshot(page, language, "public_initial"))
                page.keyboard.press("Tab")
                expect(page.locator(".skip")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#main")).to_be_focused()
                page.keyboard.press("Tab")
                expect(page.locator("#id_email")).to_be_focused()
                page.locator("form").evaluate("f=>f.noValidate=true")
                page.get_by_role(
                    "button", name="Continue" if language == "en" else "Continuar", exact=True
                ).focus()
                with page.expect_navigation(wait_until="load") as rejected:
                    page.keyboard.press("Enter")
                assert rejected.value.status == 400
                page.wait_for_load_state("load")
                record_property(
                    "fragment_focus_observed",
                    json.dumps(
                        page.evaluate(
                            "({tag:document.activeElement.tagName,id:document.activeElement.id,hash:location.hash,error_tabindex:document.querySelector('.errorlist')?.getAttribute('tabindex')})"
                        )
                    ),
                )
                record_property("reflow_partial_observations", json.dumps(observations))
                expect(page.locator(".errorlist").first).to_be_focused()
                record_property(
                    "fragment_focus_after_recovery",
                    json.dumps(
                        page.evaluate(
                            "({tag:document.activeElement.tagName,id:document.activeElement.id,hash:location.hash})"
                        )
                    ),
                )
                observations.append(snapshot(page, language, "public_required_400"))
                page.keyboard.press("Tab")
                expect(page.locator("#id_email")).to_be_focused()
                page.goto(path)
                assert page.locator("form input[name=email]").count() == 1
                page.close()
        finally:
            browser.close()
    record_property("reflow_observations", json.dumps(observations))


@pytest.mark.parametrize("language", ["es", "en"])
def test_private_reflow_content_controls_and_native_conflict(
    request, settings, live_server, language, record_property
):
    settings.DEBUG = True
    case, _, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)

    def counts():
        return [
            RightsAction.objects.filter(request=case, operation="copy_page_read").count(),
            RightsCopyPageReview.objects.filter(request=case).count(),
            RightsExport.objects.filter(action__request=case).count(),
        ]

    observations = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            for width, height in [(320, 844), (1280, 900)]:
                context = browser.new_context(viewport={"width": width, "height": height})
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
                observations.append(snapshot(page, language, "private_initial"))
                page.locator("#id_operation").select_option("compile_pages")
                page.locator("#id_reason").fill("Synthetic / private reflow fixture reason")
                with page.expect_response(lambda r: r.request.method == "POST") as rejected:
                    page.get_by_role(
                        "button",
                        name="Record copy action"
                        if language == "en"
                        else "Registrar acción de copia",
                        exact=True,
                    ).click()
                assert (
                    rejected.value.status == 409
                    and "no-store" in rejected.value.headers["cache-control"]
                )
                expect(page.locator(".errorlist").first).to_be_focused()
                observations.append(snapshot(page, language, "private_409"))
                page.goto(path)
                page.locator("#id_operation").select_option("inspect_page")
                page.locator("#id_section").select_option("subject_account")
                page.locator("#id_purpose").fill(
                    "Inspect synthetic scoped page for reflow observation"
                )
                with page.expect_response(lambda r: r.request.method == "POST") as inspected:
                    page.get_by_role(
                        "button",
                        name="Record copy action"
                        if language == "en"
                        else "Registrar acción de copia",
                        exact=True,
                    ).click()
                assert inspected.value.status == 200
                expect(page.locator("#inspection-page-output")).to_be_visible()
                assert page.locator("#page_review_entries").input_value()
                observations.append(snapshot(page, language, "private_page_read"))
                page.goto(path)
                page.reload()
                assert (
                    "Synthetic / private reflow fixture reason" not in page.content()
                    and page.locator("#inspection-page-output").count() == 0
                )
                context.close()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
    assert counts() == [2, 0, 0]
    assert db_sync(lambda: case.status) == before[0]
    record_property("reflow_observations", json.dumps(observations))
