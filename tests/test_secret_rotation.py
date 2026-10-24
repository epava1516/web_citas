"""Synthetic staged encryption rotation, immutable ciphertext and signing boundaries."""
import io
import os
import subprocess
import sys
from datetime import timedelta
from uuid import uuid4

import pyotp
import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from django.utils import timezone
from test_rights_object_store import object_store as real_object_store

from apps.core import mfa
from apps.core.encryption import encryption_cipher
from apps.core.models import User
from apps.listings.publication_state import rules_version
from apps.safety import crypto
from apps.safety.models import Report
from apps.safety.object_storage.codec import InvalidObject
from apps.safety.object_storage.repository import ObjectRepository

object_store = real_object_store


def explicit_keys(settings):
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ''
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = ''


def report(payload):
    return Report.objects.create(
        submission_key=uuid4(), receipt_digest=crypto.digest(uuid4().hex),
        payload_digest=crypto.digest('synthetic body'), encrypted_payload=crypto.seal(payload),
        mode='listing', reason='other', receipt_expires_at=timezone.now() + timedelta(days=1))


@pytest.mark.parametrize('case', ['malformed_active', 'malformed_previous', 'missing_active',
                                  'too_many', 'duplicate', 'wrong_type'])
def test_key_configuration_rejects_invalid_input_without_echo(case):
    active, previous = Fernet.generate_key().decode(), ''
    marker = 'SYNTHETIC_SECRET_MUST_NOT_APPEAR'
    if case == 'malformed_active':
        active = marker
    elif case == 'malformed_previous':
        previous = marker
    elif case == 'missing_active':
        active, previous = '', Fernet.generate_key().decode()
    elif case == 'too_many':
        previous = ','.join(Fernet.generate_key().decode() for _ in range(4))
    elif case == 'duplicate':
        previous = active
    else:
        previous = [active]
    with pytest.raises(ImproperlyConfigured) as rejected:
        encryption_cipher(active, previous)
    assert str(rejected.value) == 'Invalid encryption key configuration'
    assert marker not in str(rejected.value)


def test_bounded_predecessors_read_all_but_encrypt_only_with_active():
    active = Fernet.generate_key()
    old = [Fernet.generate_key() for _ in range(3)]
    reader = encryption_cipher(active, ','.join(k.decode() for k in old))
    for key in old:
        assert reader.decrypt(Fernet(key).encrypt(b'synthetic retained')) == b'synthetic retained'
    current = reader.encrypt(b'synthetic new')
    assert Fernet(active).decrypt(current) == b'synthetic new'
    for key in old:
        with pytest.raises(InvalidToken):
            Fernet(key).decrypt(current)


@pytest.mark.parametrize('purpose', ['MFA', 'SAFETY'])
def test_previous_keys_require_explicit_active_key(settings, purpose):
    setattr(settings, purpose + '_ENCRYPTION_KEY', '')
    setattr(settings, purpose + '_ENCRYPTION_KEY_FALLBACKS', Fernet.generate_key().decode())
    with pytest.raises(ImproperlyConfigured, match='Explicit active encryption key required'):
        (mfa.cipher if purpose == 'MFA' else crypto.cipher)()


@pytest.mark.parametrize('purpose', ['MFA', 'SAFETY'])
@pytest.mark.parametrize('field', ['active', 'previous'])
def test_startup_rejects_invalid_rotation_configuration_without_echo(purpose, field):
    env = {**os.environ, 'APP_ENV': 'development', 'DJANGO_DEBUG': '0',
           'MFA_ENCRYPTION_KEY': Fernet.generate_key().decode(),
           'SAFETY_ENCRYPTION_KEY': Fernet.generate_key().decode(),
           'MFA_ENCRYPTION_KEY_FALLBACKS': '', 'SAFETY_ENCRYPTION_KEY_FALLBACKS': ''}
    marker = 'SYNTHETIC_SECRET_MUST_NOT_APPEAR'
    name = purpose + '_ENCRYPTION_KEY' + ('_FALLBACKS' if field == 'previous' else '')
    env[name] = marker
    completed = subprocess.run([sys.executable, '-c', 'import config.settings'],
                               env=env, capture_output=True, text=True, timeout=15)
    assert completed.returncode != 0
    assert 'Invalid encryption key configuration' in completed.stderr
    assert marker not in completed.stdout + completed.stderr


@pytest.mark.django_db(transaction=True)
def test_staged_rotation_reads_old_rows_writes_new_key_and_never_rewrites_audit(settings):
    explicit_keys(settings)
    old_safety, old_mfa = settings.SAFETY_ENCRYPTION_KEY, settings.MFA_ENCRYPTION_KEY
    seed = pyotp.random_base32()
    row = report({'body': 'synthetic retained evidence'})
    user = User.objects.create_user(username='rotation-mfa', password='Synthetic-rotation!783',
                                    mfa_secret_encrypted=mfa.encrypt(seed), mfa_enabled=True)
    old_payload, old_seed = row.encrypted_payload, user.mfa_secret_encrypted
    original_digests = row.receipt_digest, row.payload_digest, mfa.recovery_digest('SYNTHETIC-RECOVERY')
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = old_safety
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = old_mfa
    assert crypto.unseal(row.encrypted_payload) == {'body': 'synthetic retained evidence'}
    assert mfa.decrypt(user.mfa_secret_encrypted) == seed
    assert mfa.consume_totp(user, pyotp.TOTP(seed).now())
    fresh = report({'body': 'synthetic new evidence'})
    fresh_seed = mfa.encrypt(seed)
    assert b'synthetic new evidence' in Fernet(settings.SAFETY_ENCRYPTION_KEY).decrypt(fresh.encrypted_payload.encode())
    assert Fernet(settings.MFA_ENCRYPTION_KEY).decrypt(fresh_seed.encode()).decode() == seed
    with pytest.raises(InvalidToken):
        Fernet(old_safety).decrypt(fresh.encrypted_payload.encode())
    with pytest.raises(InvalidToken):
        Fernet(old_mfa).decrypt(fresh_seed.encode())
    row.refresh_from_db()
    user.refresh_from_db()
    assert row.encrypted_payload == old_payload and user.mfa_secret_encrypted == old_seed
    assert (row.receipt_digest, row.payload_digest, mfa.recovery_digest('SYNTHETIC-RECOVERY')) == original_digests
    # Negative retirement witness: keeping old rows requires keeping their read key.
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ''
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = ''
    with pytest.raises(InvalidToken):
        crypto.unseal(old_payload)
    with pytest.raises(InvalidToken):
        mfa.decrypt(old_seed)
    assert crypto.unseal(fresh.encrypted_payload) == {'body': 'synthetic new evidence'}
    assert mfa.decrypt(fresh_seed) == seed
    row.refresh_from_db()
    assert row.encrypted_payload == old_payload


@pytest.mark.django_db(transaction=True)
def test_signing_rotation_revokes_session_and_changes_hmac_without_changing_explicit_cipher_keys(settings):
    explicit_keys(settings)
    settings.SECRET_KEY = 'synthetic-old-signing-' + 'a' * 50
    settings.SECRET_KEY_FALLBACKS = []
    user = User.objects.create_user(username='signing-rotation', email='rotation@example.invalid',
                                    email_verified_at=timezone.now(), password='Synthetic-signing!583')
    private = report({'body': 'synthetic evidence independent of signing key'})
    old_ciphertext = private.encrypted_payload
    old_digest = crypto.digest('synthetic receipt')
    old_recovery = mfa.recovery_digest('SYNTHETIC-RECOVERY')
    old_rules = rules_version()
    client = Client()
    client.force_login(user)
    assert client.get('/en/').wsgi_request.user.is_authenticated
    settings.SECRET_KEY = 'synthetic-new-signing-' + 'b' * 50
    assert not client.get('/en/').wsgi_request.user.is_authenticated
    assert crypto.digest('synthetic receipt') != old_digest
    assert mfa.recovery_digest('SYNTHETIC-RECOVERY') != old_recovery
    assert rules_version() != old_rules
    private.refresh_from_db()
    assert private.encrypted_payload == old_ciphertext
    assert crypto.unseal(old_ciphertext)['body'] == 'synthetic evidence independent of signing key'


def test_real_object_reference_rotation_preserves_old_bytes_and_new_key_writes(settings, object_store):
    explicit_keys(settings)
    old_key = settings.SAFETY_ENCRYPTION_KEY
    repo = ObjectRepository(object_store.client, object_store.bucket, object_store.ring, crypto.cipher())
    reference = repo.write(io.BytesIO(b'synthetic retained object'), b'rotation/retained')
    descriptor = repo.descriptor(reference)
    original = repo.client.get_object(Bucket=repo.bucket, Key=descriptor['key'])['Body'].read()
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = old_key
    transitioned = ObjectRepository(repo.client, repo.bucket, repo.ring, crypto.cipher())
    output = io.BytesIO()
    transitioned.read(reference, output, b'rotation/retained')
    assert output.getvalue() == b'synthetic retained object'
    fresh = transitioned.write(io.BytesIO(b'synthetic new object'), b'rotation/new')
    with pytest.raises(InvalidObject):
        repo.descriptor(fresh)
    assert repo.client.get_object(Bucket=repo.bucket, Key=descriptor['key'])['Body'].read() == original
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ''
    current = ObjectRepository(repo.client, repo.bucket, repo.ring, crypto.cipher())
    with pytest.raises(InvalidObject):
        current.descriptor(reference)
    output = io.BytesIO()
    current.read(fresh, output, b'rotation/new')
    assert output.getvalue() == b'synthetic new object'
