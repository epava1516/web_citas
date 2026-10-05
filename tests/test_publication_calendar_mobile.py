"""Publication queue and audited inspection through real mobile login and TOTP."""

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.db import connections
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt
from apps.safety.models import PrivacyPublicationHold, RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_queue_and_publication_inspection(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    import apps.safety.publication_purpose_release as module

    settings.DEBUG = True
    original = module.inspect
    checked = []

    def inspection_count(case_id, operation="publication_rel_read"):
        def count():
            try:
                return RightsAction.objects.filter(request_id=case_id, operation=operation).count()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(count).result(timeout=10)

    def with_mobile(user, case_id, hold_id, key, version, reason):
        if not checked:
            checked.append(True)
            # Synthetic credential provisioning; actual browser login/TOTP below.
            secret = pyotp.random_base32()
            user.mfa_secret_encrypted = encrypt(secret)
            user.save(update_fields=["mfa_secret_encrypted"])
            user.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
            credentials = json.loads((tmp_path / "credentials.json").read_text())
            root = live_server.url + f"/{language}"
            english = language == "en"
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
                )
                try:
                    page = browser.new_page(viewport={"width": 390, "height": 844})
                    page.goto(root + "/account/login/")
                    page.locator("[name=email]").fill(user.email)
                    page.locator("[name=password]").fill(credentials["password"])
                    page.locator("button[type=submit]").click()
                    page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
                    page.locator("button[type=submit]").click()
                    expect(
                        page.get_by_role(
                            "heading", name="Your account" if english else "Tu cuenta", exact=True
                        )
                    ).to_be_visible()
                    page.goto(root + "/moderation/rights/")
                    page.get_by_role(
                        "link",
                        name="Publication review calendar"
                        if english
                        else "Calendario de revisión de publicación",
                        exact=True,
                    ).click()
                    page.locator("[name=attention]").select_option("all")
                    page.get_by_role(
                        "button", name="Filter" if english else "Filtrar", exact=True
                    ).click()
                    page.get_by_role(
                        "link", name="Review measure" if english else "Revisar medida", exact=True
                    ).click()
                    detail_url = page.url
                    page.get_by_role(
                        "link",
                        name="Publication review calendar"
                        if english
                        else "Calendario de revisión de publicación",
                        exact=True,
                    ).click()
                    assert page.locator("[name=attention]").input_value() == "due"
                    page.locator("[name=attention]").select_option("all")
                    page.get_by_role(
                        "button", name="Filter" if english else "Filtrar", exact=True
                    ).click()
                    page.get_by_role(
                        "link", name="Review measure" if english else "Revisar medida", exact=True
                    ).click()
                    assert page.url == detail_url
                    follow_reason = "Seguimiento móvil sintético: conservar medida vigente."
                    page.locator("[name=operation]").select_option("follow_up")
                    page.locator("[name=reason]").fill(follow_reason)
                    page.locator("[name=next_review_on]").fill(
                        (timezone.localdate() + timedelta(days=14)).isoformat()
                    )
                    page.locator("button[type=submit]").click()
                    follow_status = "Follow-up recorded" if english else "Seguimiento registrado"
                    expect(page.get_by_role("status")).to_contain_text(follow_status)
                    assert inspection_count(case_id, "pub_cal_follow") == 1
                    page.reload()
                    expect(page.get_by_role("status")).to_contain_text(follow_status)
                    assert inspection_count(case_id, "pub_cal_follow") == 1
                    page.goto(detail_url)
                    assert follow_reason not in page.content()
                    page.locator("[name=operation]").select_option("history")
                    page.locator("[name=reason]").fill(
                        "Consulta móvil sintética del historial de seguimiento."
                    )
                    page.locator("button[type=submit]").click()
                    expect(page.locator("ol")).to_contain_text(follow_reason)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    page.goto(detail_url)
                    assert follow_reason not in page.content()
                    page.locator("[name=operation]").select_option("inspect")
                    page.locator("[name=reason]").fill(reason)
                    page.get_by_role(
                        "button",
                        name="Apply reviewed operation"
                        if english
                        else "Aplicar operación revisada",
                        exact=True,
                    ).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Inspection recorded" if english else "Consulta registrada"
                    )
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    inspections = inspection_count(case_id)
                    page.reload()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Inspection recorded" if english else "Consulta registrada"
                    )
                    assert inspection_count(case_id) == inspections
                    page.goto(page.url)
                    assert reason not in page.content()
                finally:
                    browser.close()
            hold = PrivacyPublicationHold.objects.get(pk=hold_id)
            assert hold.active and hold.version == 2
            assert hold.purpose_review_on == timezone.localdate() + timedelta(days=14)
            assert hold.initial_purpose_review_on == timezone.localdate() + timedelta(days=7)
        return original(user, case_id, hold_id, key, version, reason)

    monkeypatch.setattr(module, "inspect", with_mobile)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert checked == [True]
