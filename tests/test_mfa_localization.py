"""MFA presentation ES/EN, preserving real TOTP/recovery/session behavior."""
import re
import shutil

import pyotp
import pytest
from django.db import connection
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_agencies_mfa import PASSWORD, catalog, user_account  # noqa: F401
from test_reset_localization import db_sync

from apps.core.mfa import decrypt, recovery_digest
from apps.core.models import LegalAcceptance, LegalDocument, RecoveryCode, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_mfa_localization_and_real_enrollment_challenge_recovery(catalog, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    user = user_account('owner')
    if language == 'en':
        for document in LegalDocument.objects.filter(active=True, language='en', slug__in=['terms', 'privacy']):
            LegalAcceptance.objects.create(user=user, document=document,
                action='account_terms' if document.slug == 'terms' else 'privacy_notice')
    old_session = Client()
    old_session.force_login(user)
    invalid_code = 'Invalid code' if language == 'en' else 'Código no válido'
    heading = 'Your account' if language == 'en' else 'Tu cuenta'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            account = live_server.url + f'/{language}/account/'
            challenge = account + 'mfa/'
            enroll = challenge + 'enroll/'

            def signin():
                page.goto(account + 'login/')
                page.get_by_label(re.compile(r'^Email:?$')).fill(user.email)
                page.get_by_label(re.compile(r'^Password:?$' if language == 'en' else r'^Contraseña:?$')).fill(PASSWORD)
                page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()

            def submit():
                page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()

            def code_field():
                field = page.get_by_label(re.compile(r'^TOTP or recovery code:?$' if language == 'en' else r'^Código TOTP o recuperación:?$'))
                expect(field).to_have_attribute('autocomplete', 'one-time-code')
                return field

            def logout_signin():
                page.get_by_role('button', name='Sign out' if language == 'en' else 'Salir', exact=True).click()
                signin()
                page.wait_for_url(challenge)

            signin()
            page.wait_for_url(account)
            assert page.goto(enroll).status == 200
            password = page.get_by_label(re.compile(r'^Password:?$' if language == 'en' else r'^Contraseña:?$'))
            expect(password).to_have_attribute('autocomplete', 'current-password')
            password.fill('wrong-synthetic-password')
            submit()
            expect(page.locator('.errorlist')).to_have_text('Invalid credentials' if language == 'en' else 'Credenciales no válidas')
            expect(password).to_have_value('')
            assert not db_sync(lambda: User.objects.get(pk=user.pk).mfa_secret_encrypted)
            password.fill(PASSWORD)
            submit()
            expect(code_field()).to_be_visible()
            secret = page.locator('code').inner_text()
            encrypted = db_sync(lambda: User.objects.get(pk=user.pk).mfa_secret_encrypted)
            assert encrypted and encrypted != secret and decrypt(encrypted) == secret
            code_field().fill('not-a-valid-code')
            submit()
            expect(page.locator('.errorlist')).to_have_text(invalid_code)
            assert not db_sync(lambda: User.objects.get(pk=user.pk).mfa_enabled)
            totp = pyotp.TOTP(secret)
            code_field().fill(totp.now())
            submit()
            expect(page.get_by_role('heading', name='Save your recovery codes' if language == 'en' else 'Guarda tus códigos de recuperación', exact=True)).to_be_visible()
            codes = page.locator('code').all_inner_texts()
            assert len(codes) == 10 and len(set(codes)) == 10
            hashes = db_sync(lambda: set(RecoveryCode.objects.filter(user_id=user.pk, used_at__isnull=True).values_list('digest', flat=True)))
            assert hashes == {recovery_digest(code) for code in codes}
            previous = db_sync(lambda: old_session.get(f'/{language}/account/'))
            assert previous.status_code == 302 and previous.url == f'/{language}/account/mfa/'
            page.get_by_role('link', name='Go to account' if language == 'en' else 'Ir a mi cuenta', exact=True).click()
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            logout_signin()
            consumed_counter = db_sync(lambda: User.objects.get(pk=user.pk).mfa_last_counter)
            code_field().fill(totp.at(consumed_counter * 30))
            submit()
            expect(page.locator('.errorlist')).to_have_text(invalid_code)
            code_field().fill(codes[0])
            submit()
            page.wait_for_url(account)
            assert db_sync(lambda: RecoveryCode.objects.get(user_id=user.pk, digest=recovery_digest(codes[0])).used_at) is not None
            logout_signin()
            code_field().fill(codes[0])
            submit()
            expect(page.locator('.errorlist')).to_have_text(invalid_code)
            current_counter = totp.timecode(timezone.now())
            next_counter = max(current_counter, consumed_counter + 1)
            assert next_counter <= current_counter + 1
            code_field().fill(totp.at(next_counter * 30))
            submit()
            page.wait_for_url(account)
            page.reload()
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            logout_signin()
            code_field().fill(totp.at(next_counter * 30))
            submit()
            expect(page.locator('.errorlist')).to_have_text(invalid_code)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
