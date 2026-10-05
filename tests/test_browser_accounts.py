import os
import re
import shutil

import pytest
from django.core import mail
from django.core.management import call_command
from playwright.sync_api import expect, sync_playwright

from apps.core.models import User


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("language", ["es", "en"])
def test_real_browser_account_flow(live_server, settings, language):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")
    email = f"browser-{language}@example.invalid"
    password = "Browser-long-password!839"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.goto(f"{live_server.url}/{language}/account/signup/")
            page.locator("input[name=email]").fill(email)
            page.locator("input[name=password]").fill(password)
            page.locator("input[name=accept_terms]").check()
            page.locator("input[name=privacy_notice]").check()
            page.locator("button[type=submit]").click()
            expect(page.locator("h1")).to_have_text(
                "Check your email" if language == "en" else "Revisa tu correo"
            )
            link = re.search(r"http://localhost:8000([^\s]+)", mail.outbox[-1].body).group(1)
            page.goto(live_server.url + link)
            page.locator("button[type=submit]").click()
            expect(page).to_have_url(re.compile(r"/account/login/$"))
            page.locator("input[name=email]").fill(email)
            page.locator("input[name=password]").fill(password)
            page.locator("button[type=submit]").click()
            expect(page.locator("h1")).to_have_text(
                "Your account" if language == "en" else "Tu cuenta"
            )
            page.reload()
            expect(page.locator("h1")).to_have_text(
                "Your account" if language == "en" else "Tu cuenta"
            )
            page.locator("button[type=submit]").click()
            expect(page).to_have_url(re.compile(f"/{language}/$"))
        finally:
            browser.close()
    assert User.objects.get(email=email).email_verified_at is not None


@pytest.mark.django_db(transaction=True)
def test_browser_mfa_agency_two_people(live_server, settings):
    import pyotp
    from django.utils import timezone

    from apps.core.models import Agency, LegalAcceptance, LegalDocument

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")
    user = User.objects.create_user(
        username="browser-agency",
        email="agency@example.invalid",
        password="Browser-agency-password!382",
        email_verified_at=timezone.now(),
    )
    for doc in LegalDocument.objects.filter(
        language="es", active=True, slug__in=["terms", "privacy"]
    ):
        LegalAcceptance.objects.create(
            user=user,
            document=doc,
            action="account_terms" if doc.slug == "terms" else "privacy_notice",
        )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(live_server.url + "/es/account/login/")
            page.locator("input[name=email]").fill(user.email)
            page.locator("input[name=password]").fill("Browser-agency-password!382")
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Configurar doble factor").click()
            page.locator("input[name=password]").fill("Browser-agency-password!382")
            page.locator("button[type=submit]").click()
            secret = page.locator("code").inner_text()
            page.locator("input[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(page.locator("h1")).to_have_text("Guarda tus códigos de recuperación")
            page.get_by_role("link", name="Ir a mi cuenta").click()
            page.get_by_role("link", name="Gestión de agencia").click()
            page.locator("input[name=name]").fill("Agencia de prueba")
            page.locator("button[type=submit]").click()
            for alias in ["Persona Alfa", "Persona Beta"]:
                page.get_by_role("link", name="Añadir persona").click()
                page.locator("input[name=alias]").fill(alias)
                page.locator("button[type=submit]").click()
                expect(page.get_by_role("heading", name=alias)).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name="Persona Alfa")).to_be_visible()
            expect(page.get_by_role("heading", name="Persona Beta")).to_be_visible()
        finally:
            browser.close()
    assert Agency.objects.get(owner=user).people.count() == 2


@pytest.mark.django_db(transaction=True)
def test_browser_individual_verification(live_server, settings):
    from django.utils import timezone

    from apps.core.models import LegalAcceptance, LegalDocument, Person
    from apps.core.verification_services import publication_ready

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")
    user = User.objects.create_user(
        username="browser-verify",
        email="verify-browser@example.invalid",
        password="Browser-verify-password!936",
        email_verified_at=timezone.now(),
    )
    for document in LegalDocument.objects.filter(
        language="es", active=True, slug__in=["terms", "privacy"]
    ):
        LegalAcceptance.objects.create(
            user=user,
            document=document,
            action="account_terms" if document.slug == "terms" else "privacy_notice",
        )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.goto(live_server.url + "/es/account/login/")
            page.locator("input[name=email]").fill(user.email)
            page.locator("input[name=password]").fill("Browser-verify-password!936")
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Crear perfil particular").click()
            page.locator("input[name=alias]").fill("Particular sintético")
            page.locator("button[type=submit]").click()
            expect(page.get_by_text("Publicación bloqueada", exact=False)).to_be_visible()
            page.get_by_role("link", name="Autorizar publicación").click()
            page.locator("input[name=authorize]").check()
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Simulador de edad").click()
            page.locator("select[name=outcome]").select_option("failed")
            page.locator("button[type=submit]").click()
            expect(page.get_by_text("Publicación bloqueada", exact=False)).to_be_visible()
            page.get_by_role("link", name="Simulador de edad").click()
            page.locator("select[name=outcome]").select_option("passed")
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Comprobar teléfono").click()
            page.locator("input[name=phone]").fill("600222555")
            page.locator("button[type=submit]").click()
            page.locator("input[name=code]").fill(mail.outbox[-1].body)
            page.locator("button[type=submit]").click()
            expect(page.get_by_text("Requisitos locales completos", exact=False)).to_be_visible()
            expect(page.locator("input[name=code]")).to_have_count(0)
            page.reload()
            expect(page.get_by_text("Requisitos locales completos", exact=False)).to_be_visible()
            page.get_by_role("button", name="Revocar autorización").click()
            expect(page.get_by_text("Publicación bloqueada", exact=False)).to_be_visible()
        finally:
            browser.close()
    assert not publication_ready(Person.objects.get(subject=user))
