"""Invalid native field review requests keep localized captions and have no effects."""

import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read as read_case

from apps.core.models import User
from apps.safety.models import RightsAction
from apps.safety.rights_access_field_decision import inspect_decision, propose, review
from apps.safety.rights_access_field_read import read
from apps.safety.rights_access_scope_store import inspect

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic field decision prepared for invalid review control"


def approved_field_fixture(request, settings, monkeypatch, account_only):
    settings.DEBUG = True
    case, author, staff, _, _, _, _, _, _, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    client = operator(reviewer)
    read_case(client, case)
    inventory, manifest = inspect(
        author, case.pk, case.version, case.response_version, uuid4(), REASON
    )
    reference = next(e for e in manifest["entries"] if e["model"] == "core.User")["records"][0][
        "reference"
    ]
    original, reading = read(
        author,
        case.pk,
        case.version,
        case.response_version,
        inventory.pk,
        "core.User",
        reference,
        "email",
        uuid4(),
        REASON,
    )
    row, _ = propose(
        author,
        case.pk,
        case.version,
        case.response_version,
        inventory.pk,
        reading.pk,
        "core.User",
        reference,
        "email",
        uuid4(),
        REASON,
        "redacted",
        "[redacted]@example.invalid",
    )
    _, _, audited = inspect_decision(reviewer, case.pk, case.version, row.pk, uuid4(), REASON)
    review(reviewer, case.pk, case.version, row.pk, audited.pk, uuid4(), REASON, "approved")
    return case, author, operator(author), inventory, row


def captions(page, language):
    expect(page.locator('label[for="id_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )
    expect(page.locator('label[for="id_decisions"]')).to_have_text(
        ("Approved decision IDs" if language == "en" else "IDs de decisiones aprobadas") + ":"
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_supplement_labels_errors_audit_privacy(
    request, settings, monkeypatch, live_server, language, account_only
):
    case, author, client, inventory, row = approved_field_fixture(
        request, settings, monkeypatch, account_only
    )
    before = (case.status, case.version, case.response_version, row.encrypted_body)
    with translation.override(language):
        path = reverse("rights_access_supplement", args=[case.pk, inventory.pk])
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
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(live_server.url + path)
            captions(page, language)
            assert "[redacted]@example.invalid" not in page.content()
            for value, error in [
                ("abc", "Comma-separated IDs" if language == "en" else "IDs separados por comas"),
                (
                    f"{row.pk},{row.pk}",
                    "Unique positive IDs" if language == "en" else "IDs únicos positivos",
                ),
            ]:
                page.locator("#id_reason").fill(REASON)
                page.locator("#id_decisions").fill(value)
                with page.expect_response(lambda r: r.request.method == "POST") as response:
                    page.get_by_role(
                        "button",
                        name="Prepare supplemental copy"
                        if language == "en"
                        else "Preparar copia suplementaria",
                        exact=True,
                    ).click()
                assert response.value.status == 400
                captions(page, language)
                expect(page.get_by_text(error, exact=True)).to_be_visible()
                assert (
                    db_sync(
                        lambda: RightsAction.objects.filter(
                            request=case, operation="access_supplement"
                        ).count()
                    )
                    == 0
                )
            page.locator("#id_decisions").fill(str(row.pk))
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Prepare supplemental copy"
                    if language == "en"
                    else "Preparar copia suplementaria",
                    exact=True,
                ).click()
            assert response.value.status == 200
            expect(page.locator("pre")).to_contain_text("[redacted]@example.invalid")
            captions(page, language)
            assert (
                db_sync(
                    lambda: RightsAction.objects.filter(
                        request=case, operation="access_supplement"
                    ).count()
                )
                == 1
            )
            page.goto(live_server.url + path)
            page.reload()
            captions(page, language)
            assert "[redacted]@example.invalid" not in page.content()
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
            denied = context.request.post(
                live_server.url + path, form={"csrfmiddlewaretoken": csrf}
            )
            assert denied.status == 403
            assert denied.text() == ("Forbidden" if language == "en" else "Acceso denegado")
        finally:
            browser.close()
    case.refresh_from_db()
    row.refresh_from_db()
    assert (case.status, case.version, case.response_version, row.encrypted_body) == before
    assert RightsAction.objects.filter(request=case, operation="access_supplement").count() == 1


@pytest.mark.parametrize("language", ["es", "en"])
def test_parser_values_legacy(language):
    from apps.safety.rights_access_response_views import ReviewForm
    from apps.safety.rights_access_supplement_views import SupplementForm

    values = {
        "key": uuid4(),
        "version": 1,
        "response_version": 0,
        "reason": "Synthetic / raw untouched reason",
        "decisions": "2, 1",
    }
    form = SupplementForm(values, language=language)
    assert form.is_valid(), form.errors
    assert (
        form.cleaned_data["decisions"] == [2, 1] and form.cleaned_data["reason"] == values["reason"]
    )
    for value in ["0", "-1", "1,1", "abc"]:
        assert not SupplementForm({**values, "decisions": value}, language=language).is_valid()
    assert (
        SupplementForm().fields["decisions"].label == SupplementForm.base_fields["decisions"].label
    )
    assert ReviewForm().fields["reason"].label == ReviewForm.base_fields["reason"].label
