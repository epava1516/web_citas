from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read as read_case

from apps.core.models import User
from apps.safety.rights_access_field_decision import consume, inspect_decision, propose, review
from apps.safety.rights_access_field_read import read
from apps.safety.rights_access_scope_store import inspect
from apps.safety.tasks import purge_expired_access_field_decision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_typed_field_decisions_and_independent_review(request, settings, monkeypatch, account_only):
    case, author, _, _, _, person, subject, _, _, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    client, other = operator(author), operator(reviewer)
    read_case(other, case)
    reason = "Inspect synthetic subject field and propose disclosure"
    inventory, manifest = inspect(
        author, case.pk, case.version, case.response_version, uuid4(), reason
    )
    owner = subject if account_only else person.subject
    reference = next(entry for entry in manifest["entries"] if entry["model"] == "core.User")[
        "records"
    ][0]["reference"]
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
        reason,
    )
    assert original["value"] == owner.email
    before = case.status, case.version, case.response_version
    rows = []
    for outcome, redacted in [
        ("included", None),
        ("omitted", None),
        ("redacted", "[redacted]@example.invalid"),
    ]:
        key = uuid4()
        values = {
            "key": key,
            "version": case.version,
            "response_version": case.response_version,
            "read_id": reading.pk,
            "model": "core.User",
            "reference": reference,
            "field": "email",
            "reason": reason,
            "outcome": outcome,
            "redacted": redacted or "",
        }
        response = client.post(
            reverse("rights_access_field_prepare", args=[case.pk, inventory.pk]), values
        )
        assert response.status_code == 200, response.content.decode()
        row = response.context["decision"]
        assert row.outcome == "pending"
        assert (
            client.post(
                reverse("rights_access_field_prepare", args=[case.pk, inventory.pk]), values
            )
            .context["decision"]
            .pk
            == row.pk
        )
        path = reverse("rights_access_field_review", args=[case.pk, row.pk])
        assert path in other.get(reverse("rights_inspect", args=[case.pk])).content.decode()
        assert client.get(path).status_code == 403
        assert owner.email not in other.get(path).content.decode()
        with pytest.raises(PermissionDenied):
            inspect_decision(author, case.pk, case.version, row.pk, uuid4(), reason)
        _, body, read_action = inspect_decision(
            reviewer, case.pk, case.version, row.pk, uuid4(), reason
        )
        assert body["original"] == owner.email
        assert body["value"] == (owner.email if outcome == "included" else redacted)
        if outcome != "redacted":
            reviewed = review(
                reviewer, case.pk, case.version, row.pk, read_action.pk, uuid4(), reason, "approved"
            )
            assert reviewed.outcome == "approved"
            with pytest.raises(ValidationError, match="already reviewed"):
                review(
                    reviewer,
                    case.pk,
                    case.version,
                    row.pk,
                    read_action.pk,
                    uuid4(),
                    reason,
                    "rejected",
                )
        rows.append(row)
    with pytest.raises(ValidationError, match="foreign content"):
        propose(
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
            reason,
            "redacted",
            "forged[redacted]",
        )
    import shutil

    from django.conf import settings as django_settings
    from django.utils import translation
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    live_server = request.getfixturevalue("live_server")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": other.cookies[django_settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            for language, inspect_button, review_button in [
                ("es", "Consultar decisión", "Registrar revisión"),
                ("en", "Inspect decision", "Record review"),
            ]:
                with translation.override(language):
                    path = reverse("rights_access_field_review", args=[case.pk, rows[-1].pk])
                page.goto(live_server.url + path)
                expect(page.locator('label[for="id_reason"]')).to_have_text(
                    ("Motivo privado" if language == "es" else "Private purpose") + ":"
                )
                expect(page.locator('label[for="decision_outcome"]')).to_have_text(
                    ("Decisión" if language == "es" else "Decision") + ":"
                )
                expect(
                    page.locator('select[id="decision_outcome"] option[value="approved"]')
                ).to_have_text("Aprobar" if language == "es" else "Approve")
                assert owner.email not in page.locator("body").inner_text()
                page.locator("#id_reason").fill(reason)
                page.get_by_role("button", name=inspect_button, exact=True).click()
                expect(page.locator("section.rights-access-coverage")).to_contain_text(owner.email)
                expect(page.locator("section.rights-access-coverage")).to_contain_text(
                    "[redacted]@example.invalid"
                )
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                if language == "en":
                    page.locator("#decision_reason").fill(reason)
                    page.locator("#decision_outcome").select_option("approved")
                    page.get_by_role("button", name=review_button, exact=True).click()
                    expect(page.locator("section.rights-access-coverage")).to_contain_text(
                        "approved"
                    )
                page.goto(page.url)
                assert owner.email not in page.locator("body").inner_text()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.response_version) == before
    from apps.safety.rights_access_supplement import prepare as supplement

    supplement_key = uuid4()
    copy, copy_action = supplement(
        author,
        case.pk,
        case.version,
        case.response_version,
        inventory.pk,
        [rows[0].pk],
        supplement_key,
        reason,
    )
    assert copy["partial"] and copy["pending_fields"] and copy["pending_scopes"]
    assert copy["fields"][0]["value"] == owner.email
    assert (
        supplement(
            author,
            case.pk,
            case.version,
            case.response_version,
            inventory.pk,
            [rows[0].pk],
            supplement_key,
            reason,
        )[0]
        == copy
    )
    with pytest.raises(ValidationError, match="Conflicting decisions"):
        supplement(
            author,
            case.pk,
            case.version,
            case.response_version,
            inventory.pk,
            [rows[0].pk, rows[1].pk],
            uuid4(),
            reason,
        )
    with pytest.raises(ValidationError, match="Distinct"):
        supplement(
            author,
            case.pk,
            case.version,
            case.response_version,
            inventory.pk,
            [True],
            uuid4(),
            reason,
        )
    preview_path = reverse("rights_access_supplement", args=[case.pk, inventory.pk])
    assert client.get(preview_path).status_code == 200
    assert owner.email not in client.get(preview_path).content.decode()
    assert other.get(preview_path).status_code == 403
    response = client.post(
        preview_path,
        {
            "key": supplement_key,
            "version": case.version,
            "response_version": case.response_version,
            "decisions": str(rows[0].pk),
            "reason": reason,
        },
    )
    assert response.status_code == 200 and response.context["body"] == copy
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": client.cookies[django_settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            for language, button in [
                ("es", "Preparar copia suplementaria"),
                ("en", "Prepare supplemental copy"),
            ]:
                with translation.override(language):
                    preview_path = reverse("rights_access_supplement", args=[case.pk, inventory.pk])
                page.goto(live_server.url + preview_path)
                assert owner.email not in page.locator("body").inner_text()
                page.locator("#id_reason").fill(reason)
                page.locator("#id_decisions").fill(str(rows[0].pk))
                page.get_by_role("button", name=button, exact=True).click()
                expect(page.locator("pre.rights-copy-page")).to_contain_text(owner.email)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.goto(page.url)
                assert owner.email not in page.locator("body").inner_text()
        finally:
            browser.close()
    for row in rows:
        consumed, body, action = consume(
            author, case.pk, case.version, case.response_version, row.pk, uuid4(), reason
        )
        assert consumed.outcome == "approved" and action.operation == "access_field_use"
        assert body["preparation"]["outcome"] in {"included", "omitted", "redacted"}
    User.objects.filter(pk=reviewer.pk).update(session_version=reviewer.session_version + 1)
    with pytest.raises(PermissionDenied):
        consume(author, case.pk, case.version, case.response_version, rows[0].pk, uuid4(), reason)
    User.objects.filter(pk=reviewer.pk).update(session_version=reviewer.session_version)
    with pytest.raises(ValidationError, match="remove original"):
        propose(
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
            reason,
            "redacted",
            owner.email + "[redacted]",
        )
    for row in rows:
        row.expires_at = timezone.now() - timedelta(seconds=1)
        row.save(update_fields=["expires_at"])
    assert purge_expired_access_field_decision() == 3
    assert purge_expired_access_field_decision() == 0
    for row in rows:
        row.refresh_from_db()
        assert row.purged_at and not row.encrypted_body and row.action_id and row.read_action_id
