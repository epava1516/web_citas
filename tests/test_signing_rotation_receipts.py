"""Signing rotation revokes domain receipts, without rewriting original evidence."""
import pytest
from cryptography.fernet import Fernet
from django.contrib.auth.models import Permission
from django.test import Client
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_reports import payload as report_payload
from test_rights_intake import data as rights_payload

from apps.safety.crypto import unseal
from apps.safety.models import Report, ReportAccess, RightsAccess, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('pinned', [False, True])
@pytest.mark.parametrize('framework_fallback', [False, True])
@pytest.mark.parametrize('domain', ['report', 'rights'])
def test_signing_rotation_revokes_receipts_but_preserves_audited_evidence(
    request, settings, record_property, framework_fallback, domain, pinned
):
    original_key = 'synthetic-original-signing-' + 'a' * 64
    settings.SAFETY_HMAC_KEY = ''
    settings.SECRET_KEY = original_key
    settings.SECRET_KEY_FALLBACKS = []
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ''
    request.getfixturevalue('directory')
    client = Client()
    form, model, access = (report_payload, Report, ReportAccess) if domain == 'report' else (
        rights_payload, RightsRequest, RightsAccess)
    path = '/en/safety/' + ('report/' if domain == 'report' else 'rights/')
    data = form(client)
    response = client.post(path, data)
    assert response.status_code == 302
    case = model.objects.get()
    original = model.objects.filter(pk=case.pk).values().get()
    plaintext = unseal(original['encrypted_payload'])
    for language in ('es', 'en'):
        receipt = client.get(response.url.replace('/en/', '/' + language + '/', 1))
        assert receipt.status_code == 200 and receipt['Cache-Control'] == 'private, no-store'
    assert not access.objects.exists()
    if pinned:
        settings.SAFETY_HMAC_KEY = original_key
    settings.SECRET_KEY = 'synthetic-new-signing-' + 'b' * 64
    settings.SECRET_KEY_FALLBACKS = [original_key] if framework_fallback else []
    for language in ('es', 'en'):
        assert client.get(response.url.replace('/en/', '/' + language + '/', 1)).status_code == (200 if pinned else 404)
    assert not access.objects.exists()
    replay = client.post(path, data)
    assert replay.status_code == (302 if pinned else 409)
    if pinned:
        assert replay.url == response.url  # Same case, not a replacement intake.
    assert model.objects.count() == 1
    assert model.objects.filter(pk=case.pk).values().get() == original
    fresh = client.post(path, form(client))
    assert fresh.status_code == 302 and client.get(fresh.url).status_code == 200
    assert model.objects.count() == 2
    user, staff = reviewer()  # Fresh authenticated/MFA fixture after signing rotation.
    if domain == 'rights':
        user.user_permissions.add(Permission.objects.get(codename='review_rights_request'))
    inspection = '/en/moderation/' + ('reports/' if domain == 'report' else 'rights/') + str(case.pk) + '/'
    assert access.objects.count() == 0
    assert staff.get(inspection).status_code == 200 and access.objects.count() == 0
    viewed = staff.post(inspection, {'purpose': 'Inspect original synthetic evidence after signing rotation'})
    assert viewed.status_code == 200 and viewed['Cache-Control'] == 'private, no-store'
    assert access.objects.count() == 1
    assert model.objects.filter(pk=case.pk).values().get() == original
    assert unseal(model.objects.get(pk=case.pk).encrypted_payload) == plaintext
    record_property('old_receipts_rejected_es_en', not pinned)
    record_property('pinned_receipt_and_replay_continue_original_case', pinned)
    record_property('framework_fallback_does_not_reenable_domain_receipts', framework_fallback)
    record_property('old_submission_conflict_does_not_rebind_evidence', True)
    record_property('fresh_intake_still_available', True)
    record_property('original_row_ciphertext_and_deadlines_preserved', True)
    record_property('fresh_staff_access_requires_audit', True)
