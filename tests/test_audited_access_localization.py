"""Localized audited access on real PG sessions and TCP, preserving private reads."""
import re
import shutil

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import User
from apps.safety.models import (
    Complaint,
    ComplaintAccess,
    Report,
    ReportAccess,
    RightsAccess,
    RightsRequest,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
@pytest.mark.parametrize('family', ['report', 'complaint', 'rights'])
def test_audited_access_localization_preserves_private_post_read(directory, live_server, language, family):  # noqa: F811
    assert connection.vendor == 'postgresql'
    visitor = Client()
    suffix = {'report': 'report/', 'complaint': 'complaints/', 'rights': 'rights/'}[family]
    intake = f'/{language}/safety/' + suffix
    submitted = visitor.get(intake).context['form'].initial | {
        'reference': 'Synthetic private reference', 'explanation': 'Synthetic confidential intake explanation, not real personal data.',
        'email': 'private-inspection@example.invalid', 'name': 'Synthetic private claimant',
    }
    submitted |= {'report': {'mode': 'general', 'reason': 'other', 'good_faith': 'on'},
                  'complaint': {'relationship': 'represented'}, 'rights': {'kind': 'access'}}[family]
    assert visitor.post(intake, submitted).status_code == 302
    model, audit = {'report': (Report, ReportAccess), 'complaint': (Complaint, ComplaintAccess), 'rights': (RightsRequest, RightsAccess)}[family]
    case = model.objects.get()
    user = User.objects.get(username='fixture-v1-moderator')
    user.user_permissions.clear()
    user.groups.clear()
    permission = Permission.objects.get(codename={'report': 'review_report', 'complaint': 'review_complaint', 'rights': 'review_rights_request'}[family])
    user.user_permissions.add(permission)
    staff = Client()
    staff.force_login(user)
    session = staff.session
    session['mfa_version'] = user.mfa_version
    session.save()
    # This is a persisted synthetic authorized session, not a TOTP enrollment test.
    assert user.mfa_enabled
    path = f'/{language}/moderation/' + {'report': 'reports/', 'complaint': 'complaints/', 'rights': 'rights/'}[family] + str(case.pk) + '/'
    purpose_text = 'Review the synthetic submitted private information'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium-browser'), args=['--no-sandbox'])
        try:
            context = browser.new_context(viewport={'width': 390, 'height': 844})
            context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': staff.cookies[settings.SESSION_COOKIE_NAME].value, 'url': live_server.url}])
            page = context.new_page()
            assert page.goto(live_server.url + path).status == 200
            expect(page.get_by_label(re.compile(r'^Purpose of access:?$' if language == 'en' else r'^Motivo de consulta:?$'))).to_be_visible()
            assert submitted['email'] not in page.content()
            assert submitted['explanation'] not in page.content()
            field = page.get_by_label(re.compile(r'^Purpose of access:?$' if language == 'en' else r'^Motivo de consulta:?$'))
            field.fill('short')
            field.locator('xpath=ancestor::form').evaluate('e => e.noValidate=true')
            page.get_by_role('button', name='Record access and inspect' if language == 'en' else 'Registrar consulta y ver', exact=True).click()
            expect(page.locator('.errorlist')).to_be_visible()
            assert db_sync(lambda: audit.objects.count()) == 0
            assert submitted['email'] not in page.content()
            field.fill(purpose_text)
            with page.expect_response(lambda r: r.url == live_server.url + path and r.request.method == 'POST') as posted:
                page.get_by_role('button', name='Record access and inspect' if language == 'en' else 'Registrar consulta y ver', exact=True).click()
            assert posted.value.status == 200
            expect(page.locator('body')).to_contain_text(submitted['email'])
            assert submitted['explanation'] in page.content()
            record = db_sync(lambda: audit.objects.get())
            assert record.actor_id == user.pk and record.purpose == purpose_text and record.case_version == case.version
            # A fresh GET cannot reuse the POST's authorization to reveal plaintext.
            assert page.goto(live_server.url + path).status == 200
            assert submitted['email'] not in page.content() and submitted['explanation'] not in page.content()
            page.reload()
            assert submitted['email'] not in page.content()
            db_sync(lambda: User.objects.get(pk=user.pk).user_permissions.remove(permission))
            response = page.request.post(live_server.url + path, form={'purpose': purpose_text, 'csrfmiddlewaretoken': context.cookies()[next(i for i,c in enumerate(context.cookies()) if c['name'] == 'csrftoken')]['value']})
            assert response.status == 403
            assert response.text() == ('Forbidden' if language == 'en' else 'Acceso denegado')
            assert submitted['email'] not in response.text()
            assert db_sync(lambda: audit.objects.count()) == 1
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        finally:
            browser.close()
