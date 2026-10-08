"""Anonymous ES/EN rights intake; receipt never grants identity or data access."""
import json
import re
import shutil

import pytest
from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import RateWindow
from apps.listings.models import Listing
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccess, RightsRequest
from apps.safety.rights import fingerprint, next_month

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_rights_intake_localization_preserves_unverified_private_requests(directory, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    before = list(Listing.objects.order_by('pk').values_list('pk', 'status'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            url = live_server.url + f'/{language}/safety/rights/'
            for kind in ['representation', 'access']:
                assert page.goto(url).status == 200
                field = page.get_by_label(re.compile(r'^Right requested:?$' if language == 'en' else r'^Derecho solicitado:?$'))
                values = field.locator('option').evaluate_all('es => es.map(e=>e.value)')
                assert values == ['access', 'rectify', 'erase', 'portability', 'restriction', 'object', 'representation']
                assert field.locator('option').all_inner_texts() == (['Data access', 'Rectification', 'Erasure', 'Portability', 'Restriction', 'Objection', 'Representation complaint'] if language == 'en' else ['Acceso a datos', 'Rectificación', 'Supresión', 'Portabilidad', 'Limitación', 'Oposición', 'Reclamación de representación'])
                field.select_option(kind)
                reference = page.get_by_label(re.compile(r'^Profile or reference to your data:?$' if language == 'en' else r'^Perfil o referencia de tus datos:?$'))
                explanation = page.get_by_label(re.compile(r'^Request and scope:?$' if language == 'en' else r'^Solicitud y alcance:?$'))
                name = page.get_by_label(re.compile(r'^Name:?$' if language == 'en' else r'^Nombre:?$'))
                email = page.get_by_label(re.compile(r'^Optional private contact:?$' if language == 'en' else r'^Contacto privado opcional:?$'))
                page.locator('form').evaluate('e => e.noValidate=true')
                page.get_by_role('button', name='Submit request' if language == 'en' else 'Enviar solicitud', exact=True).click()
                expect(explanation).to_have_attribute('aria-invalid', 'true')
                expect(page.locator('.errorlist')).to_be_visible()
                assert db_sync(lambda: RightsRequest.objects.count()) == (0 if kind == 'representation' else 1)
                if kind == 'representation':
                    reference.fill('Private synthetic profile reference')
                    name.fill('Synthetic rights claimant')
                    email.fill('synthetic-rights@example.invalid')
                    explanation.fill('Private synthetic representation request without an account.')
                else:
                    explanation.fill('My data')
                    expect(reference).to_have_value('')
                    expect(email).to_have_value('')
                data = page.locator('form').evaluate('e => Object.fromEntries(new FormData(e))')
                page.get_by_role('button', name='Submit request' if language == 'en' else 'Enviar solicitud', exact=True).click()
                page.wait_for_url(re.compile(r'/safety/rights/[0-9a-f-]+/[A-Za-z0-9_-]+/$'))
                receipt_url = page.url
                heading = 'Request received' if language == 'en' else 'Solicitud recibida'
                expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
                response = page.request.get(receipt_url)
                assert response.status == 200 and response.headers['cache-control'] == 'private, no-store'
                assert response.headers['x-robots-tag'] == 'noindex, nofollow'
                for secret in ['Private synthetic profile reference', 'Synthetic rights claimant', 'synthetic-rights@example.invalid', 'Private synthetic representation request']:
                    assert secret not in page.locator('body').inner_text()
                page.reload()
                expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
                case = db_sync(lambda: RightsRequest.objects.get(submission_key=data['key']))
                assert case.kind == kind and case.priority == (0 if kind == 'representation' else 1)
                assert case.actor_id is None and case.person_id is None and case.account_subject_id is None
                assert case.scope_status == 'unverified' and case.status == 'received' and case.version == 1
                assert case.initial_due_at == next_month(case.received_at)
                payload = {key: data[key] for key in ['kind', 'reference', 'explanation', 'name', 'email']}
                assert unseal(case.encrypted_payload) == payload
                assert case.payload_digest == fingerprint(json.dumps(payload, sort_keys=True, ensure_ascii=False))
                replay = page.request.post(url, form=data, max_redirects=0)
                assert replay.status == 302 and live_server.url + replay.headers['location'] == receipt_url
                assert db_sync(lambda: RightsRequest.objects.get(pk=case.pk).initial_due_at) == case.initial_due_at
                conflict = page.request.post(url, form=data | {'kind': 'erase'})
                assert conflict.status == 409
                assert ('Conflicting request replay' if language == 'en' else 'Reintento incompatible') in conflict.text()
                assert db_sync(lambda: RightsRequest.objects.get(pk=case.pk).initial_due_at) == case.initial_due_at
                assert page.request.get(receipt_url.rsplit('/', 2)[0] + '/' + 'x' * 43 + '/').status == 404
            assert db_sync(lambda: RightsRequest.objects.count()) == 2
            assert not db_sync(lambda: RightsAccess.objects.exists())
            key = salted_hmac('rate-window', 'rights-create:127.0.0.1', algorithm='sha256').hexdigest()
            db_sync(lambda: RateWindow.objects.filter(key=key).update(attempts=20, starts_at=timezone.now()))
            rejected = page.request.post(url, form=data)
            assert rejected.status == 429
            assert rejected.text() == ('Too many requests' if language == 'en' else 'Demasiadas solicitudes')
            assert db_sync(lambda: RateWindow.objects.get(key=key).attempts) == 21
            assert db_sync(lambda: list(Listing.objects.order_by('pk').values_list('pk', 'status'))) == before
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
