"""Real mobile execution after receipt and a later scoped synthetic identity check."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt
from apps.safety.models import PrivacyHoldReleaseProposal

pytestmark = pytest.mark.django_db(transaction=True)


def localized_release_labels(page, english, publication=False):
    labels = {
        "operation": ("Operación", "Operation"),
        "ground": ("Fundamento", "Ground"),
        "resume_message_id": (
            "Mensaje del sujeto para reanudar",
            "Subject message requesting resumption",
        ),
        "proposal_id": ("Propuesta recibida", "Received proposal"),
        "reason": ("Motivo interno minimizado", "Minimized internal reason"),
    }
    if publication:
        labels.update(
            history_before=("Cursor de historial", "History cursor"),
            hold_version=("Versión de medida", "Measure version"),
            next_review_on=("Próxima revisión", "Next review"),
            read_id=("Consulta auditada", "Audited inspection"),
        )
    for name, pair in labels.items():
        expect(page.locator(f"label[for=id_{name}]")).to_have_text(pair[english] + ":")
    expected = {
        "inspect": ("Consultar medida", "Inspect restriction"),
        "propose": ("Proponer y comunicar", "Propose and notify"),
        "execute": ("Ejecutar propuesta recibida", "Execute received proposal"),
        "follow_up": ("Registrar seguimiento", "Record follow-up"),
        "history": ("Consultar historial", "Inspect history"),
    }
    actual = page.locator("[name=operation] option").evaluate_all(
        "xs=>xs.map(e=>[e.value,e.textContent])"
    )
    assert all(caption == expected[value][english] for value, caption in actual)
    assert [value for value, _ in actual if value in {"inspect", "propose", "execute"}] == [
        "inspect",
        "propose",
        "execute",
    ]


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("mode", ["restrict", "cease"])
def test_localized_mobile_execute_received_proposal(
    live_server, request, settings, monkeypatch, tmp_path, language, mode
):
    import apps.safety.publication_purpose_release as module

    settings.DEBUG = True
    original = module.execute
    checked = []

    def mobile(user, case_id, hold_id, proposal_id, key, version, reason):
        proposal = PrivacyHoldReleaseProposal.objects.select_related("response").get(pk=proposal_id)
        if not checked and hasattr(proposal.response, "receipt_acknowledgement"):
            checked.append(True)
            secret = pyotp.random_base32()
            user.mfa_secret_encrypted = encrypt(secret)
            user.save(update_fields=["mfa_secret_encrypted"])
            credentials = json.loads((tmp_path / "credentials.json").read_text())
            english = language == "en"
            root = live_server.url + f"/{language}"
            path = root + f"/moderation/rights/{case_id}/publication-purpose/{hold_id}/release/"
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
                    page.goto(path)
                    localized_release_labels(page, language == "en", True)
                    page.locator("[name=operation]").select_option("execute")
                    page.locator("[name=proposal_id]").fill(str(proposal_id))
                    page.locator("[name=reason]").fill(reason)
                    # Same idempotency key as the intercepted request; actual browser POST below.
                    page.locator("[name=key]").evaluate("(el, value) => el.value = value", str(key))
                    page.locator("[name=version]").evaluate(
                        "(el, value) => el.value = value", str(version)
                    )
                    page.locator("button[type=submit]").click()
                    status = "Release recorded" if english else "Levantamiento registrado"
                    expect(page.get_by_role("status")).to_contain_text(status)
                    page.reload()
                    expect(page.get_by_role("status")).to_contain_text(status)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    page.goto(path)
                    assert reason not in page.content()
                finally:
                    browser.close()
        return original(user, case_id, hold_id, proposal_id, key, version, reason)

    monkeypatch.setattr(module, "execute", mobile)
    import apps.safety.publication_purpose_views as views

    monkeypatch.setattr(views, "execute", mobile)
    run_flow(request, settings, monkeypatch, mode, mixed=False)
    assert checked == [True]


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("mode", ["restrict", "cease"])
def test_localized_mobile_proposal_and_public_receipt(
    live_server, request, settings, monkeypatch, tmp_path, language, mode
):
    import test_privacy_release
    from django.db import transaction

    import apps.safety.publication_purpose_release as module

    settings.DEBUG = True
    original = module.propose
    checked = []
    english = language == "en"

    def propose(
        user, case_id, hold_id, key, version, read_id, reason, ground, resume_message_id=None
    ):
        if not checked:
            # Invalid fixture cases retain the original rejection. Roll back this
            # validation so the valid proposal is actually created by the browser.
            with transaction.atomic():
                original(
                    user, case_id, hold_id, key, version, read_id, reason, ground, resume_message_id
                )
                transaction.set_rollback(True)
            checked.append(True)
            secret = pyotp.random_base32()
            user.mfa_secret_encrypted = encrypt(secret)
            user.save(update_fields=["mfa_secret_encrypted"])
            credentials = json.loads((tmp_path / "credentials.json").read_text())
            root = live_server.url + f"/{language}"
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
                    page.goto(
                        root
                        + f"/moderation/rights/{case_id}/publication-purpose/{hold_id}/release/"
                    )
                    localized_release_labels(page, language == "en", True)
                    page.locator("[name=operation]").select_option("propose")
                    page.locator("[name=read_id]").fill(str(read_id))
                    page.locator("[name=ground]").select_option(ground)
                    if resume_message_id:
                        page.locator("[name=resume_message_id]").fill(str(resume_message_id))
                    page.locator("[name=reason]").fill(reason)
                    page.locator("[name=key]").evaluate("(el, value) => el.value = value", str(key))
                    page.locator("[name=version]").evaluate(
                        "(el, value) => el.value = value", str(version)
                    )
                    page.locator("button[type=submit]").click()
                    status = "Proposal recorded" if english else "Propuesta registrada"
                    expect(page.get_by_role("status")).to_contain_text(status)
                    page.reload()
                    expect(page.get_by_role("status")).to_contain_text(status)
                finally:
                    browser.close()
        return original(
            user, case_id, hold_id, key, version, read_id, reason, ground, resume_message_id
        )

    received = []

    def confirm(client, receipt, proposal):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
            )
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                localized = f"/{language}/" + receipt.split("/", 2)[2]
                page.goto(live_server.url + localized)
                page.locator("[name=received]").check()
                page.get_by_role(
                    "button",
                    name="Record response receipt"
                    if english
                    else "Registrar recepción de respuesta",
                    exact=True,
                ).click()
                expect(
                    page.get_by_text(
                        "Receipt recorded" if english else "Recepción registrada", exact=False
                    )
                ).to_be_visible()
            finally:
                browser.close()
        proposal.response.refresh_from_db()
        assert proposal.response.receipt_acknowledgement is not None
        assert proposal.hold.active
        received.append(True)

    monkeypatch.setattr(module, "propose", propose)
    import apps.safety.publication_purpose_views as views

    monkeypatch.setattr(views, "propose", propose)
    monkeypatch.setattr(test_privacy_release, "confirm", confirm)
    run_flow(request, settings, monkeypatch, mode, mixed=False)
    assert checked == received == [True]
