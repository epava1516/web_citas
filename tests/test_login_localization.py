"""Localized login presentation, with real PostgreSQL and browser authentication."""
import re
import shutil

import pytest
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright

from apps.core.models import LegalAcceptance, LegalDocument, User

pytestmark = pytest.mark.django_db(transaction=True)
PASSWORD = 'Synthetic-login-passphrase!73'


@pytest.mark.parametrize('language', ['es', 'en'])
def test_localized_login_rejection_and_persistent_session(live_server, language):
    assert connection.vendor == 'postgresql'
    call_command('bootstrap')
    user = User.objects.create_user(username='verified', email='verified@example.invalid',
                                   password=PASSWORD, email_verified_at=timezone.now())
    User.objects.create_user(username='unverified', email='unverified@example.invalid', password=PASSWORD)
    for document in LegalDocument.objects.filter(active=True, language=language, slug__in=['terms', 'privacy']):
        LegalAcceptance.objects.create(user=user, document=document,
                                       action='account_terms' if document.slug == 'terms' else 'privacy_notice')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            path = live_server.url + f'/{language}/account/login/'
            page.goto(path)
            email = page.get_by_label(re.compile(r'^Email:?$'))
            password = page.get_by_label(re.compile(r'^Password:?$' if language == 'en' else r'^Contraseña:?$'))
            expect(email).to_have_attribute('autocomplete', 'username')
            expect(password).to_have_attribute('autocomplete', 'current-password')
            error = 'Invalid credentials' if language == 'en' else 'Credenciales no válidas'
            for address in ['unknown@example.invalid', 'unverified@example.invalid']:
                email.fill(address)
                password.fill(PASSWORD)
                with page.expect_response(lambda r: r.url == path and r.request.method == 'POST') as posted:
                    page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
                assert posted.value.status == 400
                expect(page.locator('.errorlist')).to_have_text(error)
                expect(email).to_have_value(address)
                expect(password).to_have_value('')
                assert ' / ' not in page.locator('.errorlist').inner_text()
            email.fill(user.email)
            password.fill(PASSWORD)
            page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
            page.wait_for_url(live_server.url + f'/{language}/account/')
            expect(page.get_by_role('heading', name='Your account' if language == 'en' else 'Tu cuenta', exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role('heading', name='Your account' if language == 'en' else 'Tu cuenta', exact=True)).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
