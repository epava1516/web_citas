"""Known static operation errors are localized without translating raw/error parameters."""

import shutil

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.safety.models import RightsAction, RightsCopyPageReview, RightsExport, RightsExportPreview

pytestmark = pytest.mark.django_db(transaction=True)
RAW = "Synthetic / literal purpose retained after invalid operation"


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_rejected_operations_preserve_native_gates(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    if account_only:
        case, _, staff, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, _, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)

    def counts():
        return [
            RightsAction.objects.filter(request=case).count(),
            RightsExportPreview.objects.filter(request=case).count(),
            RightsCopyPageReview.objects.filter(request=case).count(),
            RightsExport.objects.filter(action__request=case).count(),
        ]

    original = counts()
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
            page.locator("#id_operation").select_option("preview")
            page.locator("#id_purpose").fill(RAW)
            page.locator("#id_version").evaluate("(e,v)=>e.value=v", str(case.version + 1))
            with page.expect_response(lambda r: r.request.method == "POST") as stale:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert stale.value.status == 409 and "no-store" in stale.value.headers["cache-control"]
            assert page.locator(".errorlist").first.inner_text() == (
                "Request changed or purpose required"
                if language == "en"
                else "Solicitud cambiada o motivo obligatorio"
            )
            assert page.locator("#id_purpose").input_value() == RAW
            assert db_sync(counts) == original
            page.locator("#id_version").evaluate("(e,v)=>e.value=v", str(case.version))
            page.locator("#id_operation").select_option("compile_pages")
            page.locator("#id_reason").fill("Synthetic / private compilation reason")
            with page.expect_response(lambda r: r.request.method == "POST") as uncovered:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert uncovered.value.status == 409
            assert page.locator(".errorlist").first.inner_text() == (
                "Review every current section page first"
                if language == "en"
                else "Revisa primero todas las páginas de las secciones actuales"
            )
            assert db_sync(counts) == original
            page.goto(live_server.url + path)
            page.reload()
            assert RAW not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_error_catalog_preserves_unknown_messages_parameters_and_codes(language):
    from apps.safety.copy_error_presentation import operation_error

    unknown = ValidationError(
        "Synthetic / raw %(value)s",
        code="raw",
        params={"value": "Review every current section page first / data"},
    )
    known = ValidationError(
        "Review every current section page first",
        code="coverage",
        params={"token": "Synthetic / literal"},
    )
    mixed = ValidationError([unknown, known])
    result = operation_error(mixed, language)
    assert result.error_list[0] is unknown
    assert result.error_list[1].code == "coverage" and result.error_list[1].params == known.params
    assert result.error_list[1].message == (
        "Review every current section page first"
        if language == "en"
        else "Revisa primero todas las páginas de las secciones actuales"
    )
    assert (
        unknown.message == "Synthetic / raw %(value)s"
        and known.message == "Review every current section page first"
    )
    assert operation_error(unknown, language) is unknown
