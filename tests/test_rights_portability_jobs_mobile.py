"""Real Chromium ES/EN polling and canonical status fallback."""

import shutil

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Permission
from django.utils import timezone
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_jobs import REASON, enqueue, prepared
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
            token = db_sync(lambda: jobs.claim(job_id))
            assert token is not None
            expect(page.get_by_role("status")).to_have_text(
                "Validating and generating the private copy."
                if english
                else "Validando y generando la copia privada.",
                timeout=12000,
            )
            no_js.get_by_role("link", name=refresh_name).click()
            expect(no_js.get_by_role("status")).to_contain_text(
                "Validating and generating" if english else "Validando y generando"
            )
            assert page.locator("#portability-job").get_attribute("hx-get")
            db_sync(lambda: jobs.finish_attempt(job_id, token, rejected=False))
            db_sync(
                lambda: RightsPortabilityExportJob.objects.filter(pk=job_id).update(
                    available_at=timezone.now()
                )
            )
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


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("terminal_state", ["rejected", "failed"])
def test_mobile_generation_errors_stop_polling_and_offer_no_final_response(
    live_server, request, settings, monkeypatch, language, terminal_state
):
    settings.DEBUG = True
    case, author, selection, selected, *_ = prepared(request, settings, monkeypatch)
    # Give the user the final-response permission so absence of that link tests
    # the terminal error state, rather than an unrelated permission restriction.
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    job = enqueue(case, author, selection, selected)
    cookie = operator(author).cookies[django_settings.SESSION_COOKIE_NAME].value
    english = language == "en"
    url = (
        live_server.url
        + f"/{language}/moderation/rights/{case.pk}/portability/export/jobs/{job.pk}/"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            contexts = [
                browser.new_context(
                    java_script_enabled=enabled, viewport={"width": 390, "height": 844}
                )
                for enabled in (True, False)
            ]
            pages = []
            for context in contexts:
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
                page.goto(url)
                expect(page.get_by_role("status")).to_contain_text(
                    "Waiting to generate" if english else "Esperando para generar"
                )
                pages.append(page)
            attempts = 1 if terminal_state == "rejected" else jobs.MAX_ATTEMPTS
            for _ in range(attempts):
                db_sync(
                    lambda: RightsPortabilityExportJob.objects.filter(pk=job.pk).update(
                        available_at=timezone.now()
                    )
                )
                token = db_sync(lambda: jobs.claim(job.pk))
                assert token is not None
                db_sync(
                    lambda: jobs.finish_attempt(
                        job.pk, token, rejected=terminal_state == "rejected"
                    )
                )
            alert = (
                (
                    "The request or authorization changed."
                    if english
                    else "La solicitud o la autorización cambió."
                )
                if terminal_state == "rejected"
                else (
                    "The private copy could not be generated."
                    if english
                    else "No se pudo generar la copia privada."
                )
            )
            expect(pages[0].get_by_role("alert")).to_contain_text(alert, timeout=12000)
            pages[1].get_by_role(
                "link", name="Refresh status" if english else "Actualizar estado"
            ).click()
            for page in pages:
                expect(page.get_by_role("alert")).to_contain_text(alert)
                assert page.locator("#portability-job").get_attribute("hx-get") is None
                assert page.locator("#portability-job").get_attribute("hx-trigger") is None
                expect(
                    page.get_by_role(
                        "link",
                        name=("Prepare final response" if english else "Preparar respuesta final"),
                        exact=True,
                    )
                ).to_have_count(0)
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            db_sync(
                lambda: author.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            for page in pages:
                # Chromium treats this empty HTTP403 navigation as a network
                # error; retain the actual response assertion and privacy check.
                with page.expect_response(lambda response: response.url == url) as blocked:
                    try:
                        page.goto(url)
                    except PlaywrightError as error:
                        assert "net::ERR_HTTP_RESPONSE_CODE_FAILURE" in str(error)
                denied = blocked.value
                assert denied.status == 403
                assert "no-store" in denied.headers["cache-control"]
                private_body = page.request.get(url)
                assert private_body.status == 403 and private_body.body() == b""
                expect(page.locator("#portability-job")).to_have_count(0)
        finally:
            browser.close()
    job.refresh_from_db()
    assert job.state == terminal_state and job.export_id is None
    assert job.encrypted_reason == "" and job.finished_at is not None
