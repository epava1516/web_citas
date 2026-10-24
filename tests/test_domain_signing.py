"""Pinned HMAC semantics preserve legacy bytes and invalidate dependent caches."""
import os
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils.crypto import salted_hmac

from apps.core.domain_signing import domain_signing_key, validate_domain_key
from apps.listings.publication_state import rules_version
from apps.safety.crypto import digest
from apps.safety.rights import fingerprint
from apps.safety.rights_operation_fingerprints import operation_fingerprints


@pytest.mark.parametrize('value', [None, 23, b'bytes-not-config', [], 'x' * 49, ' ' * 64])
def test_invalid_domain_key_is_rejected_without_echo(value):
    with pytest.raises(ImproperlyConfigured) as error:
        validate_domain_key(value)
    assert str(error.value) == 'Domain HMAC key must be empty or an explicit strong string'


def test_empty_mode_and_exact_pin_preserve_legacy_hmac_bytes(settings):
    original = 'synthetic-legacy-domain-' + 'a' * 64
    settings.SECRET_KEY, settings.SAFETY_HMAC_KEY = original, ''
    native = salted_hmac('rights-request-v1', 'ñ😀', secret=original, algorithm='sha256').hexdigest()
    before = digest('synthetic'), fingerprint('ñ😀')
    assert before[1] == native and domain_signing_key() == original
    settings.SAFETY_HMAC_KEY = original
    settings.SECRET_KEY = 'synthetic-new-session-key-' + 'b' * 64
    assert (digest('synthetic'), fingerprint('ñ😀')) == before


@pytest.mark.django_db(transaction=True)
def test_effective_key_change_invalidates_operation_reuse_and_publication_version(settings):
    settings.SAFETY_HMAC_KEY = 'synthetic-first-domain-' + 'a' * 64
    with transaction.atomic(), operation_fingerprints():
        old, version = fingerprint('same input'), rules_version()
        assert fingerprint('same input') == old
        settings.SAFETY_HMAC_KEY = 'synthetic-second-domain-' + 'b' * 64
        new = fingerprint('same input')
        assert new != old and new == salted_hmac('rights-request-v1', 'same input',
                                                  secret=domain_signing_key(), algorithm='sha256').hexdigest()
        assert rules_version() != version


def test_startup_rejects_short_explicit_domain_key_without_echo():
    secret = 'synthetic-short-invalid'
    result = subprocess.run([sys.executable, '-c', 'import config.settings'],
                            env={**os.environ, 'APP_ENV': 'development', 'SAFETY_HMAC_KEY': secret},
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and secret not in result.stderr
    assert 'Domain HMAC key' in result.stderr
