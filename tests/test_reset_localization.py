"""Localized password replacement on real PostgreSQL and Chromium."""
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_accounts import email_path, legal_docs, verified_user  # noqa: F401

from apps.core.accounts import send_token
from apps.core.models import AccountToken

pytestmark = pytest.mark.django_db(transaction=True)
NEW_PASSWORD = 'A-new-synthetic-password!819'


def db_sync(operation):
    def isolated():
        close_old_connections()
        try:
            return operation()
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(isolated).result()


@pytest.mark.parametrize('language', ['es', 'en'])
def test_reset_localization_preserves_token_and_session_contract(legal_docs, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    user = verified_user()
    old_session = Client()
    old_session.force_login(user)
    send_token(user, 'reset', language)
    path = email_path()
    token = AccountToken.objects.get(user=user, purpose='reset', used_at__isnull=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            assert page.goto(live_server.url + path).status == 200
            password = page.get_by_label(re.compile(r'^New password:?$' if language == 'en' else r'^Nueva contraseña:?$'))
            confirm = page.get_by_label(re.compile(r'^Repeat password:?$' if language == 'en' else r'^Repetir contraseña:?$'))
            for field in [password, confirm]:
                expect(field).to_have_attribute('autocomplete', 'new-password')
            password.fill(NEW_PASSWORD)
            confirm.fill('A-different-password!873')
            page.get_by_role('button', name='Confirm' if language == 'en' else 'Confirmar', exact=True).click()
            expect(page.locator('.errorlist')).to_have_text('Passwords do not match' if language == 'en' else 'Las contraseñas no coinciden')
            for field in [password, confirm]:
                expect(field).to_have_value('')
            db_sync(token.refresh_from_db)
            assert token.used_at is None
            db_sync(user.refresh_from_db)
            assert not user.check_password(NEW_PASSWORD)
            password.fill(NEW_PASSWORD)
            confirm.fill(NEW_PASSWORD)
            page.get_by_role('button', name='Confirm' if language == 'en' else 'Confirmar', exact=True).click()
            page.wait_for_url(live_server.url + f'/{language}/account/login/')
            db_sync(user.refresh_from_db)
            db_sync(token.refresh_from_db)
            assert user.check_password(NEW_PASSWORD) and user.session_version == 1
            assert token.used_at is not None
            response = db_sync(lambda: old_session.get(f'/{language}/account/'))
            assert response.status_code == 302 and '/account/login/' in response.url
            assert page.goto(live_server.url + path).status == 400
            assert page.locator('[name="password"]').count() == 0
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
