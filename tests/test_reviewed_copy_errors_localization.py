"""Reviewed copy rejection captions preserve exact native redaction and authority."""

import json
import shutil
from copy import deepcopy

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
def test_reviewed_copy_errors_preserve_native_gates(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    if account_only:
        case, actor, staff, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, staff, _, _, _ = prepared(request, settings)
    from apps.safety.rights_exports import preview

    source = preview(actor, case.pk, case.version, RAW)
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
            malformed = deepcopy(source)
            malformed["subject_account"]["email"] = {"literal": RAW}
            identity = deepcopy(source)
            identity["subject_account"]["email"] = "different-synthetic-account@example.invalid"
            addition = {**source, "foreign_identity": RAW}
            metadata = {**source, "partial": False}
            scenarios = [
                (malformed, "Invalid reviewed copy", "Copia revisada no válida"),
                (identity, "Invalid reviewed copy", "Copia revisada no válida"),
                (addition, "Copy schema changed", "Esquema de copia cambiado"),
                (metadata, "Only text redaction allowed", "Solo se permite revisar los textos"),
            ]
            for copy, english, spanish in scenarios:
                page.goto(live_server.url + path)
                form = page.locator("form").first
                form.locator("#id_operation").select_option("generate")
                form.locator("#id_reason").fill(RAW)
                form.locator("#id_copy").fill(json.dumps(copy, ensure_ascii=False))
                with page.expect_response(lambda r: r.request.method == "POST") as denied:
                    form.get_by_role("button").click()
                assert (
                    denied.value.status == 409
                    and "no-store" in denied.value.headers["cache-control"]
                )
                assert page.locator(".errorlist").first.inner_text() == (
                    english if language == "en" else spanish
                )
                assert page.locator("#id_reason").input_value() == RAW
                assert json.loads(page.locator("#id_copy").input_value()) == copy
                assert db_sync(counts) == original
            page.goto(live_server.url + path)
            page.reload()
            assert RAW not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_finite_copy_error_catalog_and_grouping(language):
    import ast
    from pathlib import Path

    from apps.safety.copy_error_presentation import _MESSAGES, operation_error

    messages = set()
    for file, names in [
        (
            "apps/safety/rights_exports.py",
            {"reviewed_copy", "generate", "reviewer_case", "can_prepare"},
        ),
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
