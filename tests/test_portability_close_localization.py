"""Close screen presentation preserves the exact native approved text and replay."""

import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_response_draft import REASON, TEXT, operator
from test_rights_portability_response_races import ready_final_draft

from apps.safety.crypto import unseal
from apps.safety.models import RightsNotice, RightsPortabilityClosure, RightsResponse
from apps.safety.rights_portability_response_review import record
from apps.safety.rights_portability_response_views import CloseForm

pytestmark = pytest.mark.django_db(transaction=True)


def caption(page, language):
    expect(page.locator('label[for="id_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_native_approved_close_caption_errors_permission_replay(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    case, author, reviewer, _, _, draft, read_action = ready_final_draft(
        request, settings, monkeypatch, account_only=account_only
    )
    decision = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved"
    )
    staff = operator(author)
    original = (case.version, case.response_version, case.initial_due_at)
    # Use the registered route to preserve the current URL contract.
    from django.urls import reverse
    from django.utils import translation

    with translation.override(language):
        url = live_server.url + reverse(
            "rights_portability_response_close", args=[case.pk, decision.pk]
        )

    def counts():
        return [
            RightsResponse.objects.filter(request=case).count(),
            RightsNotice.objects.filter(response__request=case).count(),
            RightsPortabilityClosure.objects.filter(review=decision).count(),
        ]

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
            assert page.goto(url).status == 200
            caption(page, language)
            assert TEXT not in page.locator("body").inner_text()
            page.locator("#id_reason").fill("short")
            page.locator("form").evaluate("form=>form.noValidate=true")
            button = "Issue response and close" if language == "en" else "Emitir respuesta y cerrar"
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role("button", name=button, exact=True).click()
            assert invalid.value.status == 400
            caption(page, language)
            assert TEXT not in page.content() and db_sync(counts) == [0, 0, 0]
            csrf = page.locator("[name=csrfmiddlewaretoken]").input_value()
            db_sync(
                lambda: author.user_permissions.remove(
                    Permission.objects.get(codename="respond_rights_request")
                )
            )
            response = page.goto(url)
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = context.request.post(url, form={"csrfmiddlewaretoken": csrf})
            assert response.status == 403 and response.text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert db_sync(counts) == [0, 0, 0]
            db_sync(
                lambda: author.user_permissions.add(
                    Permission.objects.get(codename="respond_rights_request")
                )
            )
            assert page.goto(url).status == 200
            caption(page, language)
            page.locator("#id_reason").fill(REASON)
            payload = {
                name: page.locator(f'[name="{name}"]').input_value()
                for name in ["csrfmiddlewaretoken", "key", "version", "response_version", "reason"]
            }
            with page.expect_response(lambda r: r.request.method == "POST") as issued:
                page.get_by_role("button", name=button, exact=True).click()
            assert issued.value.status == 200
            expect(page.get_by_role("status")).to_contain_text(
                "Final response issued; request closed"
                if language == "en"
                else "Respuesta final emitida; solicitud cerrada"
            )
            assert TEXT not in page.content() and db_sync(counts) == [1, 1, 1]
            response = context.request.post(url, form=payload)
            assert response.status == 200 and TEXT not in response.text()
            assert db_sync(counts) == [1, 1, 1]
            page.goto(url)
            page.reload()
            assert TEXT not in page.content() and page.locator("form").count() == 0
            expect(
                page.get_by_text(
                    "Request already closed" if language == "en" else "Solicitud ya cerrada",
                    exact=True,
                )
            ).to_be_visible()
        finally:
            browser.close()
    response = RightsResponse.objects.get(request=case)
    assert unseal(response.encrypted_response) == {"text": TEXT, "simulation": True}
    closure = RightsPortabilityClosure.objects.get(review=decision)
    assert closure.review.draft_id == draft.pk and closure.response_id == response.pk
    case.refresh_from_db()
    assert case.status == "resolved" and case.scope_status == "unverified"
    assert (case.version, case.response_version, case.initial_due_at) == (
        original[0] + 1,
        original[1] + 1,
        original[2],
    )


@pytest.mark.parametrize("language", ["es", "en"])
def test_close_schema_literal_default(language):
    raw = "Literal / private synthetic close rationale"
    form = CloseForm(
        {"key": uuid4(), "version": 1, "response_version": 0, "reason": raw}, language=language
    )
    assert form.is_valid() and form.cleaned_data["reason"] == raw
    assert form.fields["reason"].max_length == 200 and form.fields["reason"].min_length == 20
    assert form.fields["version"].min_value == 1 and form.fields["response_version"].min_value == 0
    for name, field in CloseForm.base_fields.items():
        assert CloseForm().fields[name].label == field.label
