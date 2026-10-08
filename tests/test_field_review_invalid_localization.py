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
from apps.safety.rights_access_field_decision import propose
from apps.safety.rights_access_field_read import read
from apps.safety.rights_access_scope_store import inspect

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic field decision prepared for invalid review control"


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_invalid_inspection_and_decision_preserve_language(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    case, author, _, _, _, _, _, _, _, _, _ = approved_information(
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
    before = (
        case.status,
        case.version,
        case.response_version,
        row.outcome,
        row.encrypted_body,
        RightsAction.objects.filter(request=case).count(),
    )
    with translation.override(language):
        path = reverse("rights_access_field_review", args=[case.pk, row.pk])

    def captions(page):
        reason = "Private purpose" if language == "en" else "Motivo privado"
        expect(page.locator('label[for="id_reason"]')).to_have_text(reason + ":")
        expect(page.locator('label[for="decision_reason"]')).to_have_text(reason + ":")
        expect(page.locator('label[for="decision_outcome"]')).to_have_text(
            ("Decision" if language == "en" else "Decisión") + ":"
        )
        expect(page.locator('#decision_outcome option[value="approved"]')).to_have_text(
            "Approve" if language == "en" else "Aprobar"
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
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            for operation in ["inspect", "review"]:
                response = page.goto(live_server.url + path)
                assert response.status == 200
                captions(page)
                target = page.locator("form").filter(
                    has=page.locator(f'button[name="operation"][value="{operation}"]')
                )
                target.evaluate("(form)=>form.noValidate=true")
                target.locator("textarea").fill("short")
                if operation == "review":
                    target.locator("select").select_option("approved")
                with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                    target.locator("button").click()
                assert invalid.value.status == 400
                captions(page)
                assert original["value"] not in page.content()
                assert "[redacted]@example.invalid" not in page.content()
                assert (
                    db_sync(lambda: RightsAction.objects.filter(request=case).count()) == before[-1]
                )
                page.goto(live_server.url + path)
                page.reload()
                captions(page)
        finally:
            browser.close()
    case.refresh_from_db()
    row.refresh_from_db()
    assert (
        case.status,
        case.version,
        case.response_version,
        row.outcome,
        row.encrypted_body,
        RightsAction.objects.filter(request=case).count(),
    ) == before
