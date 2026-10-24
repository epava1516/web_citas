"""Proxy credentials and ledger keys have distinct authorities and lifetimes."""
import hashlib
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.test import Client
from test_recovery_ledger_codec import chain
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_object_delivery import staged

from apps.safety.models import RightsExportDownload
from apps.safety.rights_object_delivery import purge_object_deliveries
from apps.safety.rights_object_models import RightsObjectDelivery
from scripts.recovery_ledger import canonical


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('new_generation', [False, True])
def test_proxy_secret_rotation_and_optional_generation_keep_original_audit(
    request, settings, tmp_path, record_property, new_generation
):
    settings.SAFETY_HMAC_KEY = 'synthetic-independent-domain-' + 'd' * 64
    _, export, _, path, row, content = staged(request, settings, tmp_path)
    old_secret = settings.RIGHTS_DELIVERY_PROXY_SECRET
    original_audit = RightsExportDownload.objects.filter(pk=row.download_id).values().get()
    cache = tmp_path / row.object_name
    assert cache.read_bytes() == content
    settings.RIGHTS_DELIVERY_PROXY_SECRET = 'synthetic-rotated-proxy-' + 'p' * 64
    headers = {'HTTP_X_FORWARDED_URI': path, 'HTTP_X_FORWARDED_METHOD': 'GET'}
    endpoint = '/internal/rights-objects/authorize/'
    client = Client()
    assert client.get(endpoint, **headers, HTTP_X_RIGHTS_PROXY=old_secret).status_code == 404
    row.refresh_from_db()
    assert row.consumed_at is None and row.purged_at is None and cache.is_file()
    if new_generation:
        settings.RIGHTS_DELIVERY_GENERATION = 'synthetic-v2'
        assert client.get(endpoint, **headers, HTTP_X_RIGHTS_PROXY=settings.RIGHTS_DELIVERY_PROXY_SECRET).status_code == 404
        row.refresh_from_db()
        assert row.consumed_at is None and cache.is_file()
        assert purge_object_deliveries() >= 1
        row.refresh_from_db()
        assert row.purged_at is not None and not cache.exists()
        redirected = row._client.post(url(row._receipt, export), {'key': uuid4()})
        assert redirected.status_code == 303
        headers['HTTP_X_FORWARDED_URI'] = redirected['Location']
        active = RightsObjectDelivery.objects.exclude(pk=row.pk).get()
        assert active.generation == settings.RIGHTS_DELIVERY_GENERATION
    else:
        active = row
    allowed = client.get(endpoint, **headers, HTTP_X_RIGHTS_PROXY=settings.RIGHTS_DELIVERY_PROXY_SECRET)
    assert allowed.status_code == 200 and allowed['X-Delivery-Object'] == active.object_name
    assert allowed['Cache-Control'] == 'private, no-store'
    assert (tmp_path / active.object_name).read_bytes() == content
    active.refresh_from_db()
    assert active.consumed_at is not None
    assert client.get(endpoint, **headers, HTTP_X_RIGHTS_PROXY=settings.RIGHTS_DELIVERY_PROXY_SECRET).status_code == 404
    assert RightsExportDownload.objects.filter(pk=row.download_id).values().get() == original_audit
    record_property('old_proxy_secret_denied_without_consumption', True)
    record_property('fresh_proxy_secret_authorizes_one_use', True)
    record_property('original_download_audit_preserved', True)
    record_property('generation_revoked_and_physically_purged', new_generation)


def test_ledger_authority_remains_independent_of_application_key_changes(settings, record_property):
    codec, start, _, end, records = chain()
    before = hashlib.sha256(canonical(records)).hexdigest()
    payloads = codec.verify(records, start, end)
    settings.SECRET_KEY = 'synthetic-new-django-' + 's' * 64
    settings.SAFETY_HMAC_KEY = 'synthetic-new-domain-' + 'h' * 64
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    assert codec.verify(records, start, end) == payloads
    assert hashlib.sha256(canonical(records)).hexdigest() == before
    record_property('ledger_independent_keys_and_original_records_preserved', True)
