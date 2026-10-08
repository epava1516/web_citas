"""Localized account messages with real PostgreSQL, Chromium and locmem email."""
import re
import shutil

import pytest
from django.core import mail
from django.db import connection
from django.test import Client
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_acceptance_localization import replace_terms
from test_accounts import PASSWORD, email_path, legal_docs  # noqa: F401
from test_reset_localization import db_sync

from apps.core.accounts import send_token
from apps.core.models import AccountToken, LegalAcceptance, LegalDocument, RateWindow, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_signup_localized_document_gates_email_token_and_account_limits(legal_docs, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            signup = live_server.url + f'/{language}/account/signup/'

            def fill(address):
                page.get_by_label(re.compile(r'^Email:?$')).fill(address)
                page.get_by_label(re.compile(r'^Password:?$' if language == 'en' else r'^Contraseña:?$')).fill(PASSWORD)
                page.get_by_label(re.compile(r'^I accept the terms of use:?$' if language == 'en' else r'^Acepto las condiciones de uso:?$')).check()
                page.get_by_label(re.compile(r'^I have read the privacy information:?$' if language == 'en' else r'^He leído la información de privacidad:?$')).check()

            def submit():
                page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()

            assert page.goto(signup).status == 200
            fill('signup@example.invalid')
            newest = db_sync(lambda: replace_terms(language, 'dev-2'))
            submit()
            expect(page.locator('.errorlist')).to_have_text('Terms changed. Reload the form' if language == 'en' else 'Las condiciones han cambiado. Recarga el formulario')
            assert db_sync(lambda: User.objects.count()) == 0
            assert db_sync(lambda: LegalAcceptance.objects.count()) == 0
            page.goto(signup)
            fill('signup@example.invalid')
            submit()
            expect(page.get_by_role('heading', name='Check your email' if language == 'en' else 'Revisa tu correo', exact=True)).to_be_visible()
            state = db_sync(lambda: User.objects.values('pk', 'is_active', 'is_staff', 'is_superuser', 'role').get())
            assert not state['is_active'] and not state['is_staff'] and not state['is_superuser'] and state['role'] == 'visitor'
            accepted = db_sync(lambda: list(LegalAcceptance.objects.values_list('document_id', flat=True)))
            assert len(accepted) == 2 and newest.pk in accepted
            assert len(mail.outbox) == 1
            assert mail.outbox[-1].subject == ('Account confirmation' if language == 'en' else 'Confirmación de cuenta')
            assert mail.outbox[-1].body.startswith('Single-use link:\n' if language == 'en' else 'Enlace de un solo uso:\n')
            assert PASSWORD not in mail.outbox[-1].body
            path = email_path()
            assert path.startswith(f'/{language}/account/token/')
            assert page.goto(live_server.url + path).status == 200
            assert db_sync(lambda: AccountToken.objects.get(user_id=state['pk']).used_at) is None
            page.get_by_role('button', name='Confirm' if language == 'en' else 'Confirmar', exact=True).click()
            page.wait_for_url(live_server.url + f'/{language}/account/login/')
            assert db_sync(lambda: User.objects.get(pk=state['pk']).is_active)
            assert page.goto(live_server.url + path).status == 400
            db_sync(lambda: LegalDocument.objects.filter(slug='privacy', active=True).update(active=False))
            page.goto(signup)
            fill('missing-document@example.invalid')
            submit()
            expect(page.locator('.errorlist')).to_have_text('Documents unavailable' if language == 'en' else 'Documentación no disponible')
            assert db_sync(lambda: User.objects.count()) == 1
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
    # Finite HTTP check of real persisted rate windows; no repeated mail/login flood.
    user = User.objects.get(pk=state['pk'])
    send_token(user, 'reset', language)
    token_path = email_path()
    test_ip = '198.51.100.42'
    client = Client()
    routes = [('signup', 5, f'/{language}/account/signup/'),
              ('login', 10, f'/{language}/account/login/'),
              ('recover', 5, f'/{language}/account/recover/'),
              ('resend', 5, f'/{language}/account/resend/'),
              ('token', 15, token_path)]
    for action, limit, path in routes:
        key = salted_hmac('rate-window', f'{action}:{test_ip}', algorithm='sha256').hexdigest()
        RateWindow.objects.create(key=key, starts_at=timezone.now(), attempts=limit)
        response = client.post(path, {}, REMOTE_ADDR=test_ip)
        assert response.status_code == 429
        assert response.content.decode() == ('Too many attempts' if language == 'en' else 'Demasiados intentos')
        assert RateWindow.objects.get(key=key).attempts == limit + 1
    assert AccountToken.objects.get(user=user, purpose='reset', used_at__isnull=True)
