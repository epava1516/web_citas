"""Wrong ledger keys must stop recovery commands before any mutable effect."""
import base64
import hashlib
import json
from io import StringIO
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from test_erasure_execution import payload
from test_media_erasure import setup
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryApplication, RecoveryMediaJob, RecoveryOutbox
from apps.safety.rights_object_models import RightsObjectDelivery
from scripts.recovery_ledger import ZERO, Checkpoint, RecoveryLedger
from scripts.recovery_store import RecoveryStore


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('wrong_family', ['encryption', 'signing'])
def test_wrong_ledger_key_preserves_commands_data_sessions_and_files(
    request, settings, monkeypatch, tmp_path, record_property, wrong_family
):
    case, actor, _, plan, _ = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    encryption, signing = Fernet.generate_key(), b'synthetic-ledger-signing-key-' + b's' * 32
    records, authority = tmp_path / 'records', tmp_path / 'authority'
    records.mkdir(mode=0o700)
    authority.mkdir(mode=0o700)
    codec = RecoveryLedger(encryption, signing)
    store = RecoveryStore(records, authority, codec)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    store.initialize(start)
    record, end = codec.append(start, str(uuid4()), event)
    store.append(record)
    assert store.checkpoint() == end
    session = SessionStore()
    session['synthetic-control'] = 'preserve until verified recovery'
    session.save()
    settings.RECOVERY_MODE = True
    settings.RIGHTS_DELIVERY_ROOT = tmp_path / 'delivery'
    settings.RIGHTS_DELIVERY_ROOT.mkdir()
    arguments = dict(records_directory=str(records), checkpoint_directory=str(authority),
                     backup_ledger=start.ledger, backup_sequence=start.sequence, backup_head=start.head,
                     expected_ledger=end.ledger, expected_sequence=end.sequence, expected_head=end.head)

    def snapshot():
        tables = {model._meta.label: list(model.objects.order_by('pk').values())
                  for model in (Session, RecoveryApplication, RecoveryMediaJob, RecoveryOutbox, RightsObjectDelivery)}
        files = {}
        for label, root in [('records', records), ('authority', authority), ('media', Path(settings.MEDIA_ROOT))]:
            files[label] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in root.rglob('*') if p.is_file()}
        return tables, files

    before = snapshot()
    monkeypatch.setenv('RECOVERY_ENCRYPTION_KEY', (Fernet.generate_key() if wrong_family == 'encryption' else encryption).decode())
    monkeypatch.setenv('RECOVERY_SIGNING_KEY', base64.urlsafe_b64encode(
        b'synthetic-wrong-signing-' + b'x' * 32 if wrong_family == 'signing' else signing).decode())
    for command in ('check_recovery_ledger', 'apply_recovery_ledger', 'clear_recovery_sessions'):
        output = StringIO()
        with pytest.raises(CommandError):
            call_command(command, stdout=output, **arguments)
        assert output.getvalue() == '' and snapshot() == before and settings.RECOVERY_MODE
    monkeypatch.setenv('RECOVERY_ENCRYPTION_KEY', encryption.decode())
    monkeypatch.setenv('RECOVERY_SIGNING_KEY', base64.urlsafe_b64encode(signing).decode())
    output = StringIO()
    call_command('check_recovery_ledger', stdout=output, **arguments)
    verified = json.loads(output.getvalue())
    assert verified['preflight_verified'] and verified['events_checked'] == 1
    assert not verified['effects_applied'] and not verified['publication_authorized']
    assert snapshot() == before
    record_property('all_three_commands_reject_wrong_ledger_key_without_effects', True)
    record_property('sessions_ledger_authority_and_media_unchanged', True)
    record_property('retained_correct_keys_verify_original_chain_readonly', True)
