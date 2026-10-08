"""Page inspection and saved decision errors retain native gates and literal data."""

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
def test_page_read_errors_preserve_native_gates(
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
            scenarios = [
                (
                    {"operation": "inspect_page", "section": "subject_account", "page": "2"},
                    "Inspect the first page before continuing",
                    "Consulta primero la primera página antes de continuar",
                ),
                (
                    {
                        "operation": "inspect_page",
                        "section": "subject_account",
                        "page": "1",
                        "cursor": "synthetic-invalid-cursor",
                    },
                    "Invalid or expired inspection cursor",
                    "Cursor de consulta no válido o caducado",
                ),
                (
                    {"operation": "inspect_saved_page", "review_id": "2147483647"},
                    "Page review unavailable",
                    "Revisión de página no disponible",
                ),
                (
                    {
                        "operation": "inspect_page",
                        "section": "subject_account",
                        "page": "1",
                        "version": str(case.version + 1),
                    },
                    "Request changed",
                    "Solicitud cambiada",
                ),
            ]
            for overrides, english, spanish in scenarios:
                page.goto(live_server.url + path)
                form = page.locator("form").first
                form.evaluate("f=>f.noValidate=true")
                for name, value in {"purpose": RAW, **overrides}.items():
                    element = form.locator(f'[name="{name}"]')
                    if name in {"operation", "section"}:
                        element.select_option(value)
                    elif name == "cursor" or name == "version":
                        element.evaluate("(e,v)=>e.value=v", value)
                    else:
                        element.fill(value)
                with page.expect_response(lambda r: r.request.method == "POST") as denied:
                    form.get_by_role("button").click()
                assert (
                    denied.value.status == 409
                    and "no-store" in denied.value.headers["cache-control"]
                )
                assert page.locator(".errorlist").first.inner_text() == (
                    english if language == "en" else spanish
                )
                assert page.locator("#id_purpose").input_value() == RAW
                assert db_sync(counts) == original
            page.goto(live_server.url + path)
            page.reload()
            assert RAW not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_finite_page_error_catalog_and_grouping(language):
    import ast
    from pathlib import Path

    from apps.safety.copy_error_presentation import _MESSAGES, operation_error

    messages = set()
    for file, names in [
        ("apps/safety/rights_copy_inspection.py", {"inspect_page"}),
        ("apps/safety/rights_copy_page_review.py", {"inspect_saved", "record", "checked_entries"}),
    ]:
        for node in ast.parse(Path(file).read_text()).body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                messages.update(
                    call.args[0].value
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "ValidationError"
                    and call.args
                    and isinstance(call.args[0], ast.Constant)
                )
    assert messages <= _MESSAGES.keys()
    for message in messages:
        error = ValidationError(message, code="native", params={"raw": RAW})
        result = operation_error(error, language)
        assert result.code == error.code and result.params == error.params
        assert result.message == _MESSAGES[message][language == "en"]
        assert result.message and (language != "es" or result.message != message)
        assert error.message == message
    unknown = ValidationError("Synthetic / literal %(raw)s", code="raw", params={"raw": RAW})
    known = ValidationError("Page review unavailable", code="scope", params={"raw": RAW})
    grouped = operation_error(ValidationError({"read_id": [unknown, known]}), language)
    assert list(grouped.error_dict) == ["read_id"]
    assert grouped.error_dict["read_id"][0] is unknown
    assert grouped.error_dict["read_id"][1].code == "scope"
    assert grouped.error_dict["read_id"][1].params == known.params
    assert operation_error(known, None) is known
