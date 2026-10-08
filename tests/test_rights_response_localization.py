"""Generic response presentation preserves progress and recorded withdrawal semantics."""

import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_responses import TEXT, ready
from test_rights_verification import read

from apps.safety.crypto import unseal
from apps.safety.models import RightsResponse
from apps.safety.rights_actions import act
from apps.safety.rights_responses import ResponseForm

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Private operational reason for scoped synthetic response"


def captions(page, language):
    pairs = {
        "kind": ("Tipo de respuesta", "Response type"),
        "reason": ("Motivo interno", "Internal reason"),
        "response": ("Respuesta privada minimizada", "Minimized private response"),
        "redaction_confirmed": (
            "He revisado los datos de terceros y el alcance real de lo ejecutado",
            "I reviewed third-party data and actual execution scope",
        ),
    }
    for field, pair in pairs.items():
        expect(page.locator(f'label[for="id_{field}"]')).to_have_text(pair[language == "en"] + ":")


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("kind", ["access", "representation"])
def test_generic_response_screen_and_revocation(
    request, settings, monkeypatch, live_server, language, kind
):
    settings.DEBUG = True
    case, user, staff, _, _, person = ready(request, settings, monkeypatch, kind)
    if kind == "representation":
        act(
            user,
            case.pk,
            uuid4(),
            case.version,
            "withdraw",
            "Withdraw scoped representation after synthetic independent proof",
        )
        case.refresh_from_db()
        read(staff, case)
    before = (case.status, case.initial_due_at)
    path = f"/{language}/moderation/rights/{case.pk}/response/"
    selected = "representation_complete" if kind == "representation" else "progress"
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
            captions(page, language)
            if kind == "access":
                expect(page.locator("#id_kind option")).to_have_count(1)
                expect(page.locator('#id_kind option[value="progress"]')).to_have_text(
                    "Progress response" if language == "en" else "Respuesta de progreso"
                )
            else:
                expect(
                    page.locator('#id_kind option[value="representation_complete"]')
                ).to_have_text(
                    "Close withdrawn representation"
                    if language == "en"
                    else "Cerrar representación retirada"
                )
            page.locator("#id_kind").select_option(selected)
            page.locator("#id_reason").fill("short")
            page.locator("#id_response").fill(TEXT)
            page.locator("#id_redaction_confirmed").check()
            page.locator("form").evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Record motivated response"
                    if language == "en"
                    else "Registrar respuesta motivada",
                    exact=True,
                ).click()
            assert response.value.status == 400
            captions(page, language)
            assert page.locator("#id_response").input_value() == TEXT
            assert db_sync(lambda: RightsResponse.objects.filter(request=case).count()) == 0
            page.locator("#id_reason").fill(REASON)
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Record motivated response"
                    if language == "en"
                    else "Registrar respuesta motivada",
                    exact=True,
                ).click()
            assert response.value.status == 302
            assert (
                db_sync(lambda: RightsResponse.objects.filter(request=case, kind=selected).count())
                == 1
            )
            page.goto(live_server.url + path)
            page.reload()
            captions(page, language)
            assert page.locator("#id_response").input_value() == ""
            csrf = page.locator('[name="csrfmiddlewaretoken"]').input_value()
            db_sync(
                lambda: user.user_permissions.remove(
                    Permission.objects.get(codename="respond_rights_request")
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
            assert response.status == 403
            assert response.text() == ("Forbidden" if language == "en" else "Acceso denegado")
        finally:
            browser.close()
    case.refresh_from_db()
    person.refresh_from_db()
    record = RightsResponse.objects.get(request=case)
    assert unseal(record.encrypted_response)["text"] == TEXT
    assert case.response_version == 1 and case.initial_due_at == before[1]
    assert case.status == ("resolved" if kind == "representation" else before[0])
    if kind == "representation":
        assert record.withdrawal_id and person.listing.status == "withdrawn"


@pytest.mark.parametrize("language", ["es", "en"])
def test_form_values_and_legacy(language):
    data = {
        "key": uuid4(),
        "version": 1,
        "response_version": 0,
        "kind": "progress",
        "reason": REASON,
        "response": TEXT,
        "redaction_confirmed": True,
    }
    form = ResponseForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == data
    assert not ResponseForm({**data, "kind": "unsupported"}, language=language).is_valid()
    assert not ResponseForm({**data, "redaction_confirmed": False}, language=language).is_valid()
    legacy = ResponseForm()
    for name, field in ResponseForm.base_fields.items():
        assert legacy.fields[name].label == field.label
        if hasattr(field, "choices"):
            assert list(legacy.fields[name].choices) == list(field.choices)
