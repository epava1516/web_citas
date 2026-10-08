"""Private clarification ES/EN, preserving distinct complaint/rights contracts."""
import json
import re
import shutil
import uuid
from datetime import timedelta

import pytest
from django.db import connection
from django.test import Client
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import RateWindow
from apps.listings.models import Listing
from apps.safety.crypto import digest, unseal
from apps.safety.models import Complaint, ComplaintMessage, RightsMessage, RightsRequest
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
@pytest.mark.parametrize('family', ['complaint', 'rights'])
def test_private_clarification_localized_without_changing_capability_contract(directory, live_server, language, family):  # noqa: F811
    assert connection.vendor == 'postgresql'
    before = list(Listing.objects.order_by('pk').values_list('pk', 'status'))
    client = Client()
    intake = f'/{language}/safety/' + ('complaints/' if family == 'complaint' else 'rights/')
    initial = client.get(intake).context['form'].initial
    data = initial | {'reference': 'Synthetic private initial reference', 'explanation': 'Synthetic private request, not real personal information.', 'name': '', 'email': ''}
    data['relationship' if family == 'complaint' else 'kind'] = 'represented' if family == 'complaint' else 'access'
    receipt_path = client.post(intake, data).url
    case_model, message_model = (Complaint, ComplaintMessage) if family == 'complaint' else (RightsRequest, RightsMessage)
    case = case_model.objects.get()
    dates = (case.created_at, case.receipt_expires_at) if family == 'complaint' else (case.received_at, case.initial_due_at, case.receipt_expires_at)
    text = 'Synthetic private clarification of the decision reference.' if family == 'complaint' else 'My data'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            receipt = live_server.url + receipt_path
            post_url = receipt + 'message/' if family == 'complaint' else receipt
            assert page.goto(receipt).status == 200
            label = ('Private clarification' if language == 'en' else 'Aclaración privada') if family == 'complaint' else ('Clarification about your request' if language == 'en' else 'Aclaración sobre tu solicitud')
            field = page.get_by_label(re.compile('^' + re.escape(label) + ':?$'))
            expect(field).to_have_attribute('maxlength', '4000')
            field.fill('short' if family == 'complaint' else '')
            form = field.locator('xpath=ancestor::form')
            form.evaluate('e => e.noValidate=true')
            button = ('Submit reference clarification' if language == 'en' else 'Enviar aclaración de referencia') if family == 'complaint' else ('Submit clarification' if language == 'en' else 'Enviar aclaración')
            with page.expect_response(lambda r: r.url == post_url and r.request.method == 'POST') as posted:
                page.get_by_role('button', name=button, exact=True).click()
            assert posted.value.status == 400
            if family == 'complaint':
                assert page.locator('body').inner_text() == ('Invalid clarification' if language == 'en' else 'Aclaración inválida')
            else:
                expect(page.locator('.errorlist')).to_be_visible()
            assert db_sync(lambda: message_model.objects.count()) == 0
            page.goto(receipt)
            field.fill(text)
            payload = field.locator('xpath=ancestor::form').evaluate('e => Object.fromEntries(new FormData(e))')
            page.get_by_role('button', name=button, exact=True).click()
            page.wait_for_url(receipt)
            expect(field).to_be_visible()
            assert text not in page.locator('body').inner_text()
            page.reload()
            assert text not in page.locator('body').inner_text()
            row = db_sync(lambda: message_model.objects.get())
            current = db_sync(lambda: case_model.objects.get(pk=case.pk))
            assert row.actor_id is None and row.expected_version == 1
            assert text not in row.encrypted_payload and unseal(row.encrypted_payload) == {'text': text}
            signature = {'version': 1, 'text': text, 'actor': ''} if family == 'complaint' else {'case': str(case.pk), 'version': 1, 'text': text}
            signing = digest if family == 'complaint' else fingerprint
            assert row.payload_digest == signing(json.dumps(signature, sort_keys=True, ensure_ascii=False))
            assert current.version == 2 and current.status == 'received'
            current_dates = (current.created_at, current.receipt_expires_at) if family == 'complaint' else (current.received_at, current.initial_due_at, current.receipt_expires_at)
            assert dates == current_dates
            if family == 'rights':
                assert current.scope_status == 'unverified' and current.person_id is None and current.account_subject_id is None
            replay = page.request.post(post_url, form=payload, max_redirects=0)
            assert replay.status == 302
            conflict = page.request.post(post_url, form=payload | {'text': text + ' Changed.'})
            assert conflict.status == 409
            expected = ('Request changed; reload' if language == 'en' else 'Solicitud cambiada; recarga') if family == 'complaint' else ('Conflicting replay' if language == 'en' else 'Reintento incompatible')
            assert expected in conflict.text()
            stale = page.request.post(post_url, form=payload | {'key': str(uuid.uuid4())})
            assert stale.status == 409
            assert ('Request changed; reload' if language == 'en' else 'Solicitud cambiada; recarga') in stale.text()
            db_sync(lambda: case_model.objects.filter(pk=case.pk).update(status='resolved'))
            closed = page.request.post(post_url, form=payload | {'key': str(uuid.uuid4()), 'version': '2'})
            assert closed.status == 409
            db_sync(lambda: case_model.objects.filter(pk=case.pk).update(status='received'))
            assert page.request.post(post_url, form=payload | {'text': 'x' * 4001}).status == 400
            bad = receipt.rstrip('/').rsplit('/', 1)[0] + '/' + 'x' * 43 + '/'
            assert page.request.post(bad + 'message/' if family == 'complaint' else bad, form=payload).status == 404
            action = 'complaint-message:' + str(case.pk) if family == 'complaint' else 'rights-message'
            key = salted_hmac('rate-window', action + ':127.0.0.1', algorithm='sha256').hexdigest()
            db_sync(lambda: RateWindow.objects.filter(key=key).update(attempts=10, starts_at=timezone.now()))
            rejected = page.request.post(post_url, form=payload)
            assert rejected.status == 429
            assert rejected.text() == ('Too many requests' if language == 'en' else 'Demasiadas solicitudes')
            assert db_sync(lambda: RateWindow.objects.get(key=key).attempts) == 11
            db_sync(lambda: case_model.objects.filter(pk=case.pk).update(receipt_expires_at=timezone.now() - timedelta(seconds=1)))
            assert page.request.get(receipt).status == 404
            assert page.request.post(post_url, form=payload).status == 404
            assert db_sync(lambda: message_model.objects.count()) == 1
            assert db_sync(lambda: case_model.objects.get(pk=case.pk).version) == 2
            assert db_sync(lambda: list(Listing.objects.order_by('pk').values_list('pk', 'status'))) == before
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
