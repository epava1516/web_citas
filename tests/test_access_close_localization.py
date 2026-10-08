"""Access closure presentation keeps complete-delivery gates and privacy intact."""

import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import expect, sync_playwright
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_access_response_draft import REASON, TEXT
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsAccessClosure, RightsAction, RightsResponse
from apps.safety.rights_access_close_views import CloseForm
from apps.safety.rights_access_response_draft import prepare
from apps.safety.rights_access_response_review import inspect, record
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


def partial_reviewed_fixture(request, settings, monkeypatch, account_only):
    case, author, staff, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    export = generate(
        author,
        case.pk,
        uuid4(),
        case.version,
        REASON,
        preview(author, case.pk, case.version, REASON),
        information_review_id=decision.pk,
    )
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    verifier = User.objects.get(pk=verifier.pk)
    fresh(case, author, staff, verifier, operator(verifier))
    draft = prepare(
        author, case.pk, case.version, case.response_version, export.pk, uuid4(), REASON, TEXT, True
    )
    verifier.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    verifier = User.objects.get(pk=verifier.pk)
    other = operator(verifier)
    read(other, case)
    key = uuid4()
    inspect(verifier, case.pk, case.version, draft.pk, key, REASON)
    checked = record(
        verifier,
        case.pk,
        case.version,
        draft.pk,
        RightsAction.objects.get(key=key).pk,
        uuid4(),
        REASON,
        "approved",
    )
    return case, author, staff, other, checked, draft


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_close_labels_invalid_partial_and_revocation(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    case, author, staff, other, checked, draft = partial_reviewed_fixture(
        request, settings, monkeypatch, account_only
    )
    before = (
        case.status,
        case.version,
        case.response_version,
        draft.encrypted_response,
        RightsAction.objects.filter(request=case).count(),
    )
    with translation.override(language):
        path = reverse("rights_access_close", args=[case.pk, checked.pk])
    denied = other.get(path)
    assert denied.status_code == 403
    assert denied.content.decode() == ("Forbidden" if language == "en" else "Acceso denegado")

    def captions(page):
        expect(page.locator('label[for="id_reason"]')).to_have_text(
            ("Private purpose" if language == "en" else "Motivo privado") + ":"
        )

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
            captions(page)
            assert TEXT not in page.content()
            page.locator("#id_reason").fill("short")
            page.locator("form").evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Issue response and close"
                    if language == "en"
                    else "Emitir respuesta y cerrar",
                    exact=True,
                ).click()
            assert response.value.status == 400
            captions(page)
            page.locator("#id_reason").fill(REASON)
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Issue response and close"
                    if language == "en"
                    else "Emitir respuesta y cerrar",
                    exact=True,
                ).click()
            assert response.value.status == 409
            captions(page)
            expect(page.locator("body")).to_contain_text("Complete reviewed access delivery")
            assert TEXT not in page.content()
            assert db_sync(lambda: RightsResponse.objects.filter(request=case).count()) == 0
            assert (
                db_sync(lambda: RightsAccessClosure.objects.filter(action__request=case).count())
                == 0
            )
            assert db_sync(lambda: RightsAction.objects.filter(request=case).count()) == before[-1]
            page.goto(live_server.url + path)
            page.reload()
            captions(page)
            csrf = page.locator('[name="csrfmiddlewaretoken"]').input_value()
            db_sync(
                lambda: author.user_permissions.remove(
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
    draft.refresh_from_db()
    assert (
        case.status,
        case.version,
        case.response_version,
        draft.encrypted_response,
        RightsAction.objects.filter(request=case).count(),
    ) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_close_form_values_legacy(language):
    data = {
        "key": uuid4(),
        "version": 1,
        "response_version": 0,
        "reason": "Synthetic / unmodified closure purpose",
    }
    form = CloseForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == data
    assert not CloseForm({**data, "reason": "short"}, language=language).is_valid()
    assert CloseForm().fields["reason"].label == CloseForm.base_fields["reason"].label
