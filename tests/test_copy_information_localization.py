"""Copy information captions preserve ten fields, provenance, partiality and literal data."""

import shutil

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsCopyInformation
from apps.safety.rights_copy_information import FIELDS
from apps.safety.rights_copy_information_views import FieldForm, FieldSet, InformationForm, ReadForm
from apps.safety.rights_information_review_views import ReviewForm

pytestmark = pytest.mark.django_db(transaction=True)
RAW = "Synthetic / literal purpose awaiting independent assessment"
REASON = "Private synthetic information preparation rationale"


def prepare_captions(page, language):
    pairs = {
        "bind_policy": ("Vincular política mostrada", "Bind displayed policy"),
        "policy_version": ("Referencia de política", "Policy reference"),
        "reason": ("Motivo privado", "Private reason"),
        "information_id": ("Referencia de borrador", "Draft reference"),
        "purpose": ("Motivo de consulta", "Access purpose"),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    assert page.locator("fieldset").count() == 10
    for fieldset in page.locator("fieldset").all():
        for name, pair in {
            "status": ("Estado", "Status"),
            "source": ("Procedencia", "Source"),
            "text": ("Información", "Information"),
        }.items():
            expect(fieldset.locator(f'label[for$="-{name}"]')).to_have_text(
                pair[language == "en"] + ":"
            )
        expect(fieldset.locator('option[value="pending"]')).to_have_text(
            "Pending" if language == "en" else "Pendiente"
        )
        expect(fieldset.locator('option[value="unknown"]')).to_have_text(
            "Unknown" if language == "en" else "Desconocida"
        )


def review_captions(page, language):
    pairs = {
        "operation": ("Operación", "Operation"),
        "reason": ("Motivo privado", "Private reason"),
        "outcome": ("Resultado", "Outcome"),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    expect(page.locator('#id_operation option[value="inspect"]')).to_have_text(
        "Inspect" if language == "en" else "Consultar"
    )
    expect(page.locator('#id_outcome option[value="approved"]')).to_have_text(
        "Approve" if language == "en" else "Aprobar"
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_guided_information_save_read_privacy(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    if account_only:
        case, actor, staff, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)
    with translation.override(language):
        path = reverse("rights_copy_information_prepare", args=[case.pk])
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
            response = page.goto(live_server.url + path)
            assert response.status == 200
            prepare_captions(page, language)
            page.locator("#id_policy_version").fill("synthetic-ui-reference")
            page.locator("#id_reason").fill("short")
            record_form = page.locator("form").first
            record_form.evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role(
                    "button",
                    name="Save information draft"
                    if language == "en"
                    else "Guardar borrador de información",
                    exact=True,
                ).click()
            assert invalid.value.status == 400
            prepare_captions(page, language)
            assert db_sync(lambda: RightsCopyInformation.objects.filter(request=case).count()) == 0
            page.locator("#id_reason").fill(REASON)
            index = FIELDS.index("purposes")
            page.locator(f"#id_information-{index}-status").select_option("reviewed")
            page.locator(f"#id_information-{index}-source").select_option("reviewer")
            page.locator(f"#id_information-{index}-text").fill(RAW)
            with page.expect_response(lambda r: r.request.method == "POST") as saved:
                page.get_by_role(
                    "button",
                    name="Save information draft"
                    if language == "en"
                    else "Guardar borrador de información",
                    exact=True,
                ).click()
            assert saved.value.status == 200
            prepare_captions(page, language)
            assert RAW not in page.content()
            row_id = db_sync(lambda: RightsCopyInformation.objects.get(request=case).pk)
            page.locator("#id_information_id").fill(str(row_id))
            page.locator("#id_purpose").fill("Inspect current synthetic saved information")
            with page.expect_response(lambda r: r.request.method == "POST") as reading:
                page.get_by_role(
                    "button",
                    name="Inspect saved draft"
                    if language == "en"
                    else "Consultar borrador guardado",
                    exact=True,
                ).click()
            assert reading.value.status == 200
            prepare_captions(page, language)
            assert page.locator(f"#id_information-{index}-text").input_value() == RAW
            assert (
                db_sync(
                    lambda: RightsAction.objects.filter(
                        request=case, operation="copy_info_read"
                    ).count()
                )
                == 1
            )
            page.goto(live_server.url + path)
            page.reload()
            prepare_captions(page, language)
            assert RAW not in page.content()
            csrf = page.locator('[name="csrfmiddlewaretoken"]').first.input_value()
            db_sync(
                lambda: actor.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            response = page.goto(live_server.url + path)
            assert response.status == 403
            assert page.locator("body").inner_text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = context.request.post(
                live_server.url + path, form={"csrfmiddlewaretoken": csrf}
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
    row = RightsCopyInformation.objects.get(request=case)
    info = unseal(row.encrypted_information)
    assert info["access"]["purposes"]["text"] == RAW
    assert sum(item["status"] == "pending" for item in info["access"].values()) == 9
    assert row.policy_document_id is None


@pytest.mark.parametrize("language", ["es", "en"])
def test_fieldset_schema_data_and_default(language):
    fields = [
        {"field": name, "status": "pending", "source": "unknown", "text": ""} for name in FIELDS
    ]
    payload = {"information-TOTAL_FORMS": 10, "information-INITIAL_FORMS": 10}
    for index, item in enumerate(fields):
        payload.update({f"information-{index}-{key}": value for key, value in item.items()})
    formset = FieldSet(payload, prefix="information", form_kwargs={"language": language})
    assert formset.is_valid(), formset.errors
    assert formset.cleaned_data == fields
    assert (
        formset.min_num,
        formset.max_num,
        formset.absolute_max,
        formset.validate_min,
        formset.validate_max,
    ) == (10, 10, 10, True, True)
    form = FieldForm(
        {"field": "purposes", "status": "reviewed", "source": "reviewer", "text": RAW},
        language=language,
    )
    assert form.is_valid() and form.cleaned_data["text"] == RAW
    for cls in [InformationForm, FieldForm, ReadForm, ReviewForm]:
        legacy = cls()
        for name, field in cls.base_fields.items():
            assert legacy.fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(legacy.fields[name].choices) == list(field.choices)
