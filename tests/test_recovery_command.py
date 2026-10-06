import base64
import json
from io import StringIO
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.core.management.base import CommandError
from test_erasure_execution import payload
from test_media_erasure import setup
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryApplication, RecoveryMediaJob, RecoveryOutbox
from scripts.recovery_ledger import ZERO, Checkpoint, RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def test_command_requires_isolation_and_valid_authority_then_deletes_and_replays(
    request, settings, monkeypatch, tmp_path
):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    receipt = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    encryption, signing = Fernet.generate_key(), b"d" * 32
    monkeypatch.setenv("RECOVERY_ENCRYPTION_KEY", encryption.decode())
    monkeypatch.setenv("RECOVERY_SIGNING_KEY", base64.urlsafe_b64encode(signing).decode())
    records, authority = tmp_path / "records", tmp_path / "authority"
    records.mkdir(mode=0o700)
    authority.mkdir(mode=0o700)
    codec = RecoveryLedger(encryption, signing)
    store = RecoveryStore(records, authority, codec)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    store.initialize(start)
    encoded, _ = codec.append(start, str(uuid4()), receipt)
    store.append(encoded)
    arguments = dict(
        records_directory=str(records),
        checkpoint_directory=str(authority),
        backup_ledger=start.ledger,
        backup_sequence=0,
        backup_head=ZERO,
        media_limit=100,
    )
    original, derivative = blob.original.name, blob.derivative.name
    settings.RECOVERY_MODE = False
    with pytest.raises(CommandError):
        call_command("apply_recovery_ledger", **arguments)
    assert not RecoveryApplication.objects.exists() and blob.original.storage.exists(original)
    settings.RECOVERY_MODE = True
    with pytest.raises(CommandError):
        call_command("apply_recovery_ledger", **(arguments | {"media_limit": 101}))
    assert not RecoveryApplication.objects.exists()
    checkpoint = authority / "checkpoint.json"
    saved = checkpoint.read_bytes()
    checkpoint.unlink()
    with pytest.raises(CommandError):
        call_command("apply_recovery_ledger", **arguments)
    assert not RecoveryApplication.objects.exists() and blob.original.storage.exists(original)
    checkpoint.write_bytes(saved)
    checkpoint.chmod(0o600)
    output = StringIO()
    call_command("apply_recovery_ledger", stdout=output, **arguments)
    result = json.loads(output.getvalue())
    assert result == {
        "applied": 1,
        "pending_media_jobs": 0,
        "publication_authorized": False,
        "media_completed": 1,
        "exhausted_media_jobs": 0,
    }
    assert not blob.original.storage.exists(original)
    assert not blob.derivative.storage.exists(derivative)
    assert settings.RECOVERY_MODE
    output = StringIO()
    call_command("apply_recovery_ledger", stdout=output, **arguments)
    assert json.loads(output.getvalue())["applied"] == 0
    assert RecoveryApplication.objects.count() == RecoveryMediaJob.objects.count() == 1
