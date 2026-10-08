"""Static copy preparation captions preserve audited source and page decisions."""

import json
import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
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
from apps.safety.models import RightsAction, RightsCopyPageReview, RightsExport, RightsExportPreview
from apps.safety.rights_exports import ExportForm, PageReviewForm

pytestmark = pytest.mark.django_db(transaction=True)
PURPOSE = "Synthetic / literal audited copy inspection purpose"
REASON = "Synthetic / private page review reason preserved literally"


def captions(page, language):
    for name, pair in {
        "operation": ("Operación", "Operation"),
        "purpose": ("Motivo de consulta", "Access purpose"),
        "reason": ("Motivo privado de entrega", "Private release reason"),
        "section": ("Sección", "Section"),
        "page": ("Página", "Page"),
        "review_id": ("Referencia de revisión", "Review reference"),
    }.items():
        expect(page.locator("form").first.locator(f'label[for="id_{name}"]')).to_have_text(
            pair[language == "en"] + ":"
        )
    expect(page.locator('#id_operation option[value="preview"]')).to_have_text(
        "Preview copy (audited)" if language == "en" else "Consultar copia (auditoría)"
    )
    expect(page.locator('#id_section option[value="subject_account"]')).to_have_text(
        "Subject account" if language == "en" else "Cuenta del titular"
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_audited_preparation_and_page_decisions(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    if account_only:
        case, actor, staff, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, staff, _, _, person = prepared(request, settings)
        subject = person.subject
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
            captions(page, language)
            assert subject.email not in page.content()
            button = page.get_by_role(
                "button",
                name="Record copy action" if language == "en" else "Registrar acción de copia",
                exact=True,
            )
            page.locator("form").first.evaluate("f=>f.noValidate=true")
            page.locator("#id_operation").select_option("preview")
            page.locator("#id_purpose").fill("short")
            # Optional purpose's native min length applies to supplied values.
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                button.click()
            assert invalid.value.status == 400
            captions(page, language)
            assert db_sync(lambda: RightsExportPreview.objects.filter(request=case).count()) == 0
            page.locator("#id_purpose").fill(PURPOSE)
            with page.expect_response(lambda r: r.request.method == "POST") as valid:
                button.click()
            assert valid.value.status == 200
            captions(page, language)
            data = json.loads(page.locator("#id_copy").input_value())
            assert data["subject_account"]["email"] == subject.email
            assert db_sync(lambda: RightsExportPreview.objects.filter(request=case).count()) == 1
            # Rerender retains opaque operation codes and native audited page reads.
            page.locator("#id_operation").select_option("inspect_page")
            page.locator("#id_section").select_option("subject_account")
            page.locator("#id_page").fill("1")
            page.locator("#id_purpose").fill(PURPOSE)
            with page.expect_response(lambda r: r.request.method == "POST") as inspected:
                button.click()
            assert inspected.value.status == 200
            captions(page, language)
            review_form = page.locator("form").filter(
                has=page.get_by_role(
                    "button",
                    name="Save page decisions"
                    if language == "en"
                    else "Guardar decisiones de página",
                    exact=True,
                )
            )
            expect(review_form.locator('label[for="id_reason"]')).to_have_text(
                "Private review reason:" if language == "en" else "Motivo privado de revisión:"
            )
            entries = json.loads(review_form.locator("#id_entries").input_value())
            assert entries[0]["email"] == subject.email
            review_form.evaluate("f=>f.noValidate=true")
            review_form.locator("#id_reason").fill("short")
            with page.expect_response(lambda r: r.request.method == "POST") as bad_review:
                review_form.get_by_role("button").click()
            assert bad_review.value.status == 400
            expect(page.locator('label[for="id_reason"]')).to_have_text(
                "Private review reason:" if language == "en" else "Motivo privado de revisión:"
            )
            assert db_sync(lambda: RightsCopyPageReview.objects.filter(request=case).count()) == 0
            page.locator("#id_reason").fill(REASON)
            with page.expect_response(lambda r: r.request.method == "POST") as saved:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert saved.value.status == 200
            captions(page, language)
            row_id = db_sync(lambda: RightsCopyPageReview.objects.get(request=case).pk)
            page.locator("#id_operation").select_option("inspect_saved_page")
            page.locator("#id_review_id").fill(str(row_id))
            page.locator("#id_purpose").fill(PURPOSE)
            with page.expect_response(lambda r: r.request.method == "POST") as saved_read:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert saved_read.value.status == 200
            assert subject.email in page.locator("#saved-page-output").inner_text()
            page.goto(live_server.url + path)
            page.reload()
            captions(page, language)
            assert subject.email not in page.content() and REASON not in page.content()
            csrf = page.locator('[name="csrfmiddlewaretoken"]').first.input_value()
            db_sync(
                lambda: actor.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            # Read-only form remains available; action permission is checked natively.
            assert page.goto(live_server.url + path).status == 200
            action_denied = context.request.post(
                live_server.url + path,
                form={
                    "csrfmiddlewaretoken": csrf,
                    "key": str(uuid4()),
                    "version": str(case.version),
                    "operation": "preview",
                    "purpose": PURPOSE,
                },
            )
            assert (
                action_denied.status == 403 and "no-store" in action_denied.headers["cache-control"]
            )
            db_sync(
                lambda: actor.user_permissions.remove(
                    Permission.objects.get(codename="review_rights_request")
                )
            )
            denied = page.goto(live_server.url + path)
            assert denied.status == 403 and "no-store" in denied.headers["cache-control"]
            expected = "Forbidden" if language == "en" else "Acceso denegado"
            assert page.locator("body").inner_text() == expected
            denied = context.request.post(
                live_server.url + path, form={"csrfmiddlewaretoken": csrf}
            )
            assert denied.status == 403 and denied.text() == expected
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
    row = RightsCopyPageReview.objects.get(request=case)
    assert unseal(row.encrypted_entries) == entries
    assert unseal(row.action.encrypted_reason)["reason"] == REASON
    assert RightsExport.objects.filter(action__request=case).count() == 0
    assert RightsAction.objects.filter(request=case, operation="copy_page_read").count() == 1


@pytest.mark.parametrize("language", ["es", "en"])
def test_schema_and_literal_json_unchanged(language):
    raw = {"literal": "Synthetic / bilingual raw content"}
    for cls in [ExportForm, PageReviewForm]:
        with CaptureQueriesContext(connection) as queries:
            legacy = cls()
            localized = cls(language=language)
        assert len(queries) == 0
        for name, field in cls.base_fields.items():
            assert legacy.fields[name].label == field.label
            assert localized.fields[name].required == field.required
            if hasattr(field, "choices"):
                assert [v for v, _ in legacy.fields[name].choices] == [
                    v for v, _ in localized.fields[name].choices
                ]
        assert legacy.fields["version"].min_value == localized.fields["version"].min_value == 1
    payload = {"key": str(uuid4()), "version": 1, "operation": "generate", "copy": json.dumps(raw)}
    a = ExportForm(payload)
    b = ExportForm(payload, language=language)
    assert a.is_valid() and b.is_valid() and a.cleaned_data == b.cleaned_data
    assert b.cleaned_data["copy"] == raw and b.fields["reason"].max_length == 2000
