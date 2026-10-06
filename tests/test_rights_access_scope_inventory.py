from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information

from apps.core.models import User
from apps.safety.models import RightsAction
from apps.safety.rights_access_scope_store import inspect

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_field_inventory_is_scoped_opaque_stable_and_detects_subject_changes(
    request, settings, monkeypatch, account_only
):
    case, author, _, _, _, person, subject, _, _, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    reason = "Audit synthetic subject record scope before access coverage"
    key = uuid4()
    import apps.safety.rights_access_scope_store as module

    real_source = module.source

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="access_scope_read").exists()
        return real_source(*args)

    monkeypatch.setattr(module, "source", audited)
    row, manifest = inspect(author, case.pk, case.version, case.response_version, key, reason)
    assert (
        inspect(author, case.pk, case.version, case.response_version, key, reason)[0].pk == row.pk
    )
    assert manifest["digest"] == row.source_digest
    assert manifest["current_procedure_excluded"] and manifest["pending"]
    assert not any(
        entry["count"]
        for entry in manifest["entries"]
        if entry["model"]
        in ["safety.RightsRequest", "safety.RightsAction", "safety.RightsAccessScopeInventory"]
    )
    owner = subject if account_only else person.subject
    user_entry = next(entry for entry in manifest["entries"] if entry["model"] == "core.User")
    assert user_entry["count"] == 1 and "password" in user_entry["fields"]
    assert owner.password not in str(manifest)
    assert owner.email not in str(manifest)
    assert "core.User.groups" in [entry["model"] for entry in manifest["entries"]]
    before = case.version, case.response_version, case.status
    from django.test import Client
    from django.urls import reverse
    from test_rights_portability_response_draft import operator

    path = reverse("rights_access_scope", args=[case.pk])
    client = operator(author)
    assert path in client.get(reverse("rights_inspect", args=[case.pk])).content.decode()
    actions = RightsAction.objects.count()
    response = client.get(path)
    assert response.status_code == 200 and manifest["digest"] not in response.content.decode()
    assert "no-store" in response["Cache-Control"]
    assert RightsAction.objects.count() == actions
    assert Client().get(path).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(author)
    assert csrf.post(path, {}).status_code == 403
    values = {
        "key": key,
        "version": case.version,
        "response_version": case.response_version,
        "reason": reason,
        "page": 1,
    }
    response = client.post(path, values)
    assert response.status_code == 200 and manifest["digest"] in response.content.decode()
    assert len(response.context["entries"]) <= 25
    response = client.post(path, values | {"page": 2})
    assert response.status_code == 200 and response.context["entries"].number == 2
    assert RightsAction.objects.count() == actions
    assert manifest["digest"] not in client.get(path).content.decode()
    assert owner.email not in response.content.decode()
    from apps.safety.rights_access_field_read import read

    target = user_entry["records"][0]["reference"]
    field_key = uuid4()
    body, field_action = read(
        author,
        case.pk,
        case.version,
        case.response_version,
        row.pk,
        "core.User",
        target,
        "email",
        field_key,
        reason,
    )
    assert body["value"] == owner.email and field_action.operation == "access_field_read"
    assert (
        read(
            author,
            case.pk,
            case.version,
            case.response_version,
            row.pk,
            "core.User",
            target,
            "email",
            field_key,
            reason,
        )[0]
        == body
    )
    with pytest.raises(ValidationError, match="Conflicting"):
        read(
            author,
            case.pk,
            case.version,
            case.response_version,
            row.pk,
            "core.User",
            target,
            "first_name",
            field_key,
            reason,
        )
    with pytest.raises(ValidationError, match="Unsupported"):
        read(
            author,
            case.pk,
            case.version,
            case.response_version,
            row.pk,
            "core.User",
            target,
            "password",
            uuid4(),
            reason,
        )
    with pytest.raises(ValidationError, match="Exact inventoried"):
        read(
            author,
            case.pk,
            case.version,
            case.response_version,
            row.pk,
            "core.User",
            "0" * 64,
            "email",
            uuid4(),
            reason,
        )
    response = client.post(
        path, values | {"field_target": f"core.User|{target}|email", "field_key": field_key}
    )
    assert response.status_code == 200 and owner.email in response.content.decode()
    assert owner.email not in client.get(path).content.decode()
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
                        "value": client.cookies[django_settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            browser_page = context.new_page()
            for language, button, next_button in [
                ("es", "Registrar consulta y ver", "Siguiente"),
                ("en", "Record access and inspect", "Next"),
            ]:
                with translation.override(language):
                    browser_path = reverse("rights_access_scope", args=[case.pk])
                browser_page.goto(live_server.url + browser_path)
                assert manifest["digest"] not in browser_page.locator("body").inner_text()
                browser_page.locator("#id_reason").fill(reason)
                browser_page.get_by_role("button", name=button, exact=True).click()
                expect(browser_page.locator("body")).to_contain_text(manifest["digest"])
                browser_page.get_by_role("button", name=next_button, exact=True).click()
                expect(browser_page.locator("body")).to_contain_text(manifest["digest"])
                assert browser_page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                browser_page.get_by_role("button", name=button, exact=True).click()
                email_button = browser_page.locator(
                    f'button[name="field_target"][value="core.User|{target}|email"]'
                )
                for _ in range(10):
                    if email_button.count():
                        break
                    browser_page.get_by_role("button", name=next_button, exact=True).click()
                assert email_button.count() == 1
                browser_page.locator("details").filter(has=email_button).locator("summary").click()
                email_button.click()
                expect(browser_page.locator("aside.rights-copy-page")).to_contain_text(owner.email)
                assert browser_page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                browser_page.goto(browser_page.url)
                assert manifest["digest"] not in browser_page.locator("body").inner_text()
                assert owner.email not in browser_page.locator("body").inner_text()
        finally:
            browser.close()
    # A field omitted by the older erasure projection must still change access scope.
    User.objects.filter(pk=owner.pk).update(last_name="Changed synthetic subject identity")
    from django.db import transaction

    with transaction.atomic():
        assert real_source(case, None if account_only else person)["digest"] != manifest["digest"]
    # Account identity proof or the profile snapshot can reject the changed source first.
    with pytest.raises(ValidationError, match="Identity and scope|inventory changed"):
        inspect(author, case.pk, case.version, case.response_version, key, reason)
    User.objects.filter(pk=owner.pk).update(last_name=owner.last_name)
    assert inspect(author, case.pk, case.version, case.response_version, key, reason)[1] == manifest
    stale = User.objects.get(pk=author.pk)
    User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
    with pytest.raises(PermissionDenied):
        inspect(stale, case.pk, case.version, case.response_version, key, reason)
    User.objects.filter(pk=author.pk).update(session_version=author.session_version)
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status) == before
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_access_scope_inventory

    references = row.action_id, row.request_id, row.proof_id, row.source_digest
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_access_scope_inventory() == 1
    assert purge_expired_access_scope_inventory() == 0
    row.refresh_from_db()
    assert row.purged_at and not row.encrypted_inventory
    assert (row.action_id, row.request_id, row.proof_id, row.source_digest) == references
