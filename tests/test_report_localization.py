"""Public report ES/EN, preserving formal rules, privacy and stable payloads."""
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
from apps.safety.crypto import digest, unseal
from apps.safety.models import Report, Restriction, UrgentReportAlert

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_report_presentation_and_formal_exception_preserve_private_intake(directory, live_server, language):  # noqa: F811
    assert connection.vendor == 'postgresql'
    before = list(Listing.objects.order_by('pk').values_list('pk', 'status'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            url = live_server.url + f'/{language}/safety/report/'
            for variant in ['general', 'formal', 'exception']:
                assert page.goto(url).status == 200
                mode = page.get_by_label(re.compile(r'^Report type:?$' if language == 'en' else r'^Tipo de denuncia:?$'))
                reason = page.get_by_label(re.compile(r'^Reason:?$' if language == 'en' else r'^Motivo:?$'))
                assert mode.locator('option').evaluate_all('es => es.map(e=>e.value)') == ['general', 'formal']
                assert reason.locator('option').evaluate_all('es => es.map(e=>e.value)') == ['minor', 'exploitation', 'nonconsent', 'illegal', 'fraud', 'other']
                assert mode.locator('option').all_inner_texts() == (['General report', 'Formal notice'] if language == 'en' else ['Denuncia general', 'Notificación formal'])
                assert reason.locator('option').all_inner_texts() == (['Minors', 'Exploitation', 'Without consent', 'Illegal content', 'Fraud', 'Other'] if language == 'en' else ['Menores', 'Explotación', 'Sin consentimiento', 'Contenido ilícito', 'Fraude', 'Otro'])
                mode.select_option('general' if variant == 'general' else 'formal')
                reason.select_option('nonconsent')
                reference = page.get_by_label(re.compile(r'^Exact URL or reference:?$' if language == 'en' else r'^URL o referencia exacta:?$'))
                explanation = page.get_by_label(re.compile(r'^Explanation:?$' if language == 'en' else r'^Explicación:?$'))
                name = page.get_by_label(re.compile(r'^Notifier name:?$' if language == 'en' else r'^Nombre del notificante:?$'))
                email = page.get_by_label(re.compile(r'^Private contact:?$' if language == 'en' else r'^Contacto privado:?$'))
                exception = page.get_by_label(re.compile(r'^Notice concerning offences in Articles 3–7 of Directive 2011/93/EU:?$' if language == 'en' else r'^Notificación sobre delitos de los artículos 3–7 de la Directiva 2011/93/UE:?$'))
                faith = page.get_by_label(re.compile(r'^I declare in good faith that the information is accurate and complete:?$' if language == 'en' else r'^Declaro de buena fe que la información es precisa y completa:?$'))
                reference.fill('Synthetic private reference')
                explanation.fill('Synthetic private report, without personal or graphic real content.')
                faith.check()
                if variant == 'formal':
                    page.get_by_role('button', name='Send report' if language == 'en' else 'Enviar denuncia', exact=True).click()
                    expect(name).to_have_attribute('aria-invalid', 'true')
                    expect(email).to_have_attribute('aria-invalid', 'true')
                    errors = page.locator('.errorlist').all_inner_texts()
                    assert errors == ['Required for formal notice' if language == 'en' else 'Obligatorio para notificación formal'] * 2
                    assert db_sync(lambda: Report.objects.count()) == 1
                    name.fill('Synthetic notifier')
                    email.fill('synthetic-notifier@example.invalid')
                elif variant == 'exception':
                    exception.check()
                data = page.locator('form').evaluate('e => Object.fromEntries(new FormData(e))')
                page.get_by_role('button', name='Send report' if language == 'en' else 'Enviar denuncia', exact=True).click()
                page.wait_for_url(re.compile(r'/safety/receipt/[0-9a-f-]+/[A-Za-z0-9_-]+/$'))
                receipt_url = page.url
                heading = 'Report received' if language == 'en' else 'Denuncia recibida'
                expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
                response = page.request.get(receipt_url)
                assert response.status == 200 and response.headers['cache-control'] == 'private, no-store'
                assert response.headers['x-robots-tag'] == 'noindex, nofollow'
                for sensitive in ['Synthetic notifier', 'synthetic-notifier@example.invalid', data['explanation'], data['reference']]:
                    assert sensitive not in page.locator('body').inner_text()
                page.reload()
                expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
                report = db_sync(lambda: Report.objects.get(submission_key=data['key']))
                assert report.actor_id is None and report.priority == 0 and report.reason == 'nonconsent'
                assert report.mode == ('general' if variant == 'general' else 'formal')
                assert db_sync(lambda: UrgentReportAlert.objects.filter(report_id=report.pk).count()) == 1
                payload = {key: data.get(key, '') for key in ['target', 'mode', 'reason', 'reference', 'explanation', 'name', 'email']}
                payload.update(exception=variant == 'exception', good_faith=True)
                assert unseal(report.encrypted_payload) == payload
                assert report.payload_digest == digest(json.dumps(payload, sort_keys=True, ensure_ascii=False))
                replay = page.request.post(url, form=data, max_redirects=0)
                assert replay.status == 302 and live_server.url + replay.headers['location'] == receipt_url
                conflict = page.request.post(url, form=data | {'explanation': 'Different synthetic report reusing the submission key.'})
                assert conflict.status == 409
                assert ('Conflicting request replay' if language == 'en' else 'Solicitud repetida incompatible') in conflict.text()
                assert page.request.get(receipt_url.rsplit('/', 2)[0] + '/' + 'x' * 43 + '/').status == 404
            assert db_sync(lambda: Report.objects.count()) == 3
            assert db_sync(lambda: UrgentReportAlert.objects.count()) == 3
            bad_target = page.request.post(url, form=data | {'target': 'invalid-synthetic-signed-target'})
            assert bad_target.status == 400
            assert ('Invalid or expired reference' if language == 'en' else 'Referencia inválida o caducada') in bad_target.text()
            key = salted_hmac('rate-window', 'report-create:127.0.0.1', algorithm='sha256').hexdigest()
            db_sync(lambda: RateWindow.objects.filter(key=key).update(attempts=20, starts_at=timezone.now()))
            rejected = page.request.post(url, form=data)
            assert rejected.status == 429
            assert rejected.text() == ('Too many requests' if language == 'en' else 'Demasiadas solicitudes')
            assert db_sync(lambda: RateWindow.objects.get(key=key).attempts) == 21
            assert db_sync(lambda: list(Listing.objects.order_by('pk').values_list('pk', 'status'))) == before
            assert not db_sync(lambda: Restriction.objects.exists())
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
