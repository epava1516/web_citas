"""Presentation of updated synthetic terms, preserving version acceptance gates."""
import re
import shutil

import pytest
from django.db import connection, transaction
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_accounts import PASSWORD, legal_docs, verified_user  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import LegalAcceptance, LegalDocument

pytestmark = pytest.mark.django_db(transaction=True)


def replace_terms(language, version):
    with transaction.atomic():
        LegalDocument.objects.filter(language=language, slug='terms', active=True).update(active=False)
        return LegalDocument.objects.create(slug='terms', language=language, version=version,
            title='Synthetic updated terms', body='Synthetic document; not legally approved.', published_at=timezone.now())


@pytest.mark.parametrize('language', ['es', 'en'])
def test_localized_acceptance_preserves_stale_version_and_missing_document_gates(legal_docs, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    user = verified_user()
    originals = list(LegalDocument.objects.filter(active=True, language=language, slug__in=['terms', 'privacy']))
    for document in originals:
        LegalAcceptance.objects.create(user=user, document=document,
            action='account_terms' if document.slug == 'terms' else 'privacy_notice')
    old_terms = next(document for document in originals if document.slug == 'terms')
    intermediate = replace_terms(language, 'dev-2')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            account = live_server.url + f'/{language}/account/'
            accept = account + 'accept/'
            page.goto(account + 'login/')
            page.get_by_label(re.compile(r'^Email:?$')).fill(user.email)
            page.get_by_label(re.compile(r'^Password:?$' if language == 'en' else r'^Contraseña:?$')).fill(PASSWORD)
            page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
            page.wait_for_url(accept)
            terms = page.get_by_label(re.compile(r'^I accept the terms of use:?$' if language == 'en' else r'^Acepto las condiciones de uso:?$'))
            privacy = page.get_by_label(re.compile(r'^I have read the privacy information:?$' if language == 'en' else r'^He leído la información de privacidad:?$'))
            terms.check()
            privacy.check()
            expect(page.locator('[name="version_terms"]')).to_have_value('dev-2')
            newest = db_sync(lambda: replace_terms(language, 'dev-3'))
            with page.expect_response(lambda r: r.url == accept and r.request.method == 'POST') as posted:
                page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
            assert posted.value.status == 400
            expect(page.locator('.errorlist')).to_have_text('Documents updated. Reload' if language == 'en' else 'Documentos actualizados. Recarga')
            assert db_sync(lambda: LegalAcceptance.objects.filter(user_id=user.pk, document_id__in=[intermediate.pk, newest.pk]).count()) == 0
            # Refresh via a new GET, rather than resubmitting the stale POST.
            assert page.goto(accept).status == 200
            expect(page.locator('[name="version_terms"]')).to_have_value('dev-3')
            terms.check()
            privacy.check()
            page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
            page.wait_for_url(account)
            heading = 'Your account' if language == 'en' else 'Tu cuenta'
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            assert db_sync(lambda: LegalAcceptance.objects.filter(user_id=user.pk, document_id=newest.pk).count()) == 1
            assert db_sync(lambda: LegalAcceptance.objects.filter(user_id=user.pk, document_id=old_terms.pk).count()) == 1
            count = db_sync(lambda: LegalAcceptance.objects.filter(user_id=user.pk).count())
            db_sync(lambda: LegalDocument.objects.filter(slug='privacy', active=True).update(active=False))
            page.goto(account)
            page.wait_for_url(accept)
            terms.check()
            privacy.check()
            page.get_by_role('button', name='Continue' if language == 'en' else 'Continuar', exact=True).click()
            expect(page.locator('.errorlist')).to_have_text('Documents unavailable' if language == 'en' else 'Documentos no disponibles')
            assert db_sync(lambda: LegalAcceptance.objects.filter(user_id=user.pk).count()) == count
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
