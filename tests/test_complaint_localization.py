"""Anonymous complaint ES/EN presentation with real PostgreSQL and TCP browser."""
import json
import re
import shutil

import pytest
from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_complaint_intake import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import RateWindow
from apps.listings.models import Listing
from apps.safety.crypto import digest, unseal
from apps.safety.models import Complaint, Report, Restriction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_anonymous_complaint_localization_preserves_private_intake(directory, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    before = list(Listing.objects.order_by('pk').values_list('pk', 'status'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            url = live_server.url + f'/{language}/safety/complaints/'
            assert page.goto(url).status == 200
            relationship = page.get_by_label(re.compile(r'^Your stated relationship:?$' if language == 'en' else r'^Relación que declaras:?$'))
            options = relationship.locator('option').evaluate_all('es => es.map(e => [e.value, e.textContent])')
            assert [value for value, _ in options] == ['represented', 'advertiser', 'notifier', 'other']
            assert [text for _, text in options] == (['Represented person', 'Advertiser', 'Notifier', 'Other relationship'] if language == 'en' else ['Persona representada', 'Anunciante', 'Notificante', 'Otra relación'])
            relationship.select_option('represented')
            reference = page.get_by_label(re.compile(r'^Decision or profile reference:?$' if language == 'en' else r'^Decisión o perfil al que te refieres:?$'))
            explanation = page.get_by_label(re.compile(r'^Why you request review:?$' if language == 'en' else r'^Por qué solicitas revisión:?$'))
            name = page.get_by_label(re.compile(r'^Name:?$' if language == 'en' else r'^Nombre:?$'))
            contact = page.get_by_label(re.compile(r'^Your private contact:?$' if language == 'en' else r'^Contacto privado propio:?$'))
            reference.fill('Synthetic private reference')
            name.fill('Synthetic claimant')
            contact.fill('synthetic-claimant@example.invalid')
            explanation.fill('short')
            page.locator('form').evaluate('e => e.noValidate = true')
            page.get_by_role('button', name='Send review request' if language == 'en' else 'Enviar reclamación', exact=True).click()
            expect(page.locator('.errorlist')).to_be_visible()
            expect(explanation).to_have_attribute('aria-invalid', 'true')
            error_id = explanation.get_attribute('aria-describedby')
            assert error_id and page.locator('#' + error_id).is_visible()
            assert db_sync(lambda: Complaint.objects.count()) == 0
            body = 'Synthetic private review by a represented person without an account.'
            explanation.fill(body)
            data = page.locator('form').evaluate('e => Object.fromEntries(new FormData(e))')
            page.get_by_role('button', name='Send review request' if language == 'en' else 'Enviar reclamación', exact=True).click()
            page.wait_for_url(re.compile(r'/safety/complaints/[0-9a-f-]+/[A-Za-z0-9_-]+/$'))
            receipt_url = page.url
            receipt = page.request.get(receipt_url)
            assert receipt.status == 200
            assert receipt.headers['cache-control'] == 'private, no-store'
            assert receipt.headers['x-robots-tag'] == 'noindex, nofollow'
            heading = 'Review request received' if language == 'en' else 'Reclamación recibida'
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            for sensitive in [body, data['reference'], data['name'], data['email']]:
                assert sensitive not in page.locator('body').inner_text()
            page.reload()
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            case = db_sync(lambda: Complaint.objects.get())
            assert case.actor_id is None and case.status == 'received' and case.version == 1
            payload = {k: data[k] for k in ['relationship', 'reference', 'explanation', 'name', 'email']}
            assert unseal(case.encrypted_payload) == payload
            expected_digest = digest(json.dumps({'payload': payload, 'actor': ''}, sort_keys=True, ensure_ascii=False))
            assert case.payload_digest == expected_digest
            assert data['email'] not in case.encrypted_payload
            replay = page.request.post(url, form=data, max_redirects=0)
            assert replay.status == 302 and live_server.url + replay.headers['location'] == receipt_url
            assert db_sync(lambda: Complaint.objects.count()) == 1
            conflict = page.request.post(url, form=data | {'explanation': 'Another request with the same submission key.'})
            assert conflict.status == 409
            text = conflict.text()
            assert ('Conflicting replay' if language == 'en' else 'Reintento incompatible') in text
            assert ' / ' not in re.search(r'<ul class="errorlist nonfield".*?</ul>', text, re.S).group()
            wrong_receipt = receipt_url.rsplit('/', 2)[0] + '/' + 'x' * 43 + '/'
            assert page.request.get(wrong_receipt).status == 404
            key = salted_hmac('rate-window', 'complaint-create:127.0.0.1', algorithm='sha256').hexdigest()
            db_sync(lambda: RateWindow.objects.filter(key=key).update(attempts=10, starts_at=timezone.now()))
            rejected = page.request.post(url, form=data)
            assert rejected.status == 429
            assert rejected.text() == ('Too many requests' if language == 'en' else 'Demasiadas solicitudes')
            assert db_sync(lambda: RateWindow.objects.get(key=key).attempts) == 11
            assert db_sync(lambda: list(Listing.objects.order_by('pk').values_list('pk', 'status'))) == before
            assert not db_sync(lambda: Report.objects.exists() or Restriction.objects.exists())
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
