"""Real Chromium ES/EN polling and canonical status fallback."""

import shutil

import pytest
from django.conf import settings as django_settings
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_jobs import REASON, prepared
from test_rights_portability_response_draft import operator

from apps.safety import rights_portability_jobs as jobs
from apps.safety.models import RightsPortabilityExportJob

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_generation_polling_and_no_javascript_fallback(
    live_server, request, settings, monkeypatch, language
):
    settings.DEBUG = True
    case, author, _, selected, *_ = prepared(request, settings, monkeypatch)
    staff = operator(author)
    cookie = staff.cookies[django_settings.SESSION_COOKIE_NAME].value
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/export/"
            )
            page.locator("#id_review").select_option(str(selected.pk))
            page.locator("#id_reason").fill(REASON)
            page.get_by_role(
                "button",
                name="Create approved private copy" if english else "Crear copia privada aprobada",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_have_text(
                "Waiting to generate the private copy."
                if english
                else "Esperando para generar la copia privada."
            )
            assert page.locator("#portability-job").get_attribute("hx-get")
            canonical = page.url
            # A separate browser without JavaScript can inspect and refresh pending work.
            fallback = browser.new_context(
                java_script_enabled=False, viewport={"width": 390, "height": 844}
            )
            fallback.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            no_js = fallback.new_page()
            no_js.goto(canonical)
            expect(no_js.get_by_role("status")).to_contain_text(
                "Waiting to generate" if english else "Esperando para generar"
            )
            refresh_name = "Refresh status" if english else "Actualizar estado"
            expect(no_js.get_by_role("link", name=refresh_name)).to_be_visible()
            job_id = db_sync(lambda: RightsPortabilityExportJob.objects.get().pk)
            db_sync(lambda: jobs.run(job_id))
            expect(page.get_by_role("status")).to_contain_text(
                "Private copy created" if english else "Copia privada creada", timeout=12000
            )
            assert page.locator("#portability-job").get_attribute("hx-get") is None
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            no_js.get_by_role("link", name=refresh_name).click()
            expect(no_js.get_by_role("status")).to_contain_text(
                "Private copy created" if english else "Copia privada creada"
            )
            context.close()
            fallback.close()
        finally:
            browser.close()
