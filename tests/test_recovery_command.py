import base64
import hashlib
import json
from datetime import timedelta
from io import StringIO
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from test_erasure_execution import payload
from test_media_erasure import setup
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare as prepare_inventory
from apps.safety.erasure_plans import record as record_plan
from apps.safety.models import (
    RecoveryApplication,
    RecoveryMediaJob,
    RecoveryOutbox,
    RightsExportDownload,
)
from apps.safety.rights_object_models import RightsObjectDelivery
from scripts.recovery_ledger import ZERO, Checkpoint, RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def test_command_requires_isolation_and_valid_authority_then_deletes_and_replays(
    request, settings, monkeypatch, tmp_path
):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    settings.RIGHTS_DELIVERY_ROOT = tmp_path / 'delivery-cache'
    settings.RIGHTS_DELIVERY_ROOT.mkdir()
    cached = b'synthetic restored private bytes; not a released rights copy'
    download = RightsExportDownload.objects.get(export__action__request=case)
    delivery = RightsObjectDelivery.objects.create(
        download=download, generation='synthetic-restored-generation', object_name=uuid4().hex,
        content_sha256=hashlib.sha256(cached).hexdigest(), content_bytes=len(cached),
        content_type='application/json; charset=utf-8', filename='synthetic.json',
        binding_digest='a' * 64, expires_at=timezone.now() + timedelta(days=1))
    delivery_file = settings.RIGHTS_DELIVERY_ROOT / delivery.object_name
    delivery_file.write_bytes(cached)
    # The added cache is a new resource: repeat inventory and review normally.
    snapshot = prepare_inventory(actor, case.pk, uuid4(), case.version,
                                 'Review current resources including synthetic delivery cache')
    decisions = unseal(plan.encrypted_decisions)['decisions']
    plan = record_plan(actor, case.pk, snapshot.pk, uuid4(), case.version, decisions)
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
    expected = store.checkpoint()
    arguments = dict(
        expected_ledger=expected.ledger,
        expected_sequence=expected.sequence,
        expected_head=expected.head,
        records_directory=str(records),
        checkpoint_directory=str(authority),
        backup_ledger=start.ledger,
        backup_sequence=0,
        backup_head=ZERO,
        media_limit=100,
    )
    original, derivative = blob.original.name, blob.derivative.name
    for marker in ["synthetic-restored-subject", "synthetic-restored-moderator"]:
        session = SessionStore()
        session["synthetic_marker"] = marker
        session.save()
    session_count = Session.objects.count()
    assert session_count >= 2
    settings.RECOVERY_MODE = False
    session_arguments = {k: v for k, v in arguments.items() if k != "media_limit"}
    with pytest.raises(CommandError):
        call_command("clear_recovery_sessions", **session_arguments)
    assert Session.objects.count() == session_count
    with pytest.raises(CommandError):
        call_command("apply_recovery_ledger", **arguments)
    assert not RecoveryApplication.objects.exists() and blob.original.storage.exists(original)
    settings.RECOVERY_MODE = True
    with pytest.raises(CommandError):
        call_command("clear_recovery_sessions", **session_arguments)
    assert Session.objects.count() == session_count
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
    delivery.refresh_from_db()
    assert delivery.purged_at is not None, 'Recovery command left a restored grant unpurged'
    assert not delivery_file.exists(), 'Recovery command retained restored private delivery bytes'
    assert RightsExportDownload.objects.filter(pk=download.pk).exists()
    assert not blob.original.storage.exists(original)
    assert not blob.derivative.storage.exists(derivative)
    assert settings.RECOVERY_MODE
    application = RecoveryApplication.objects.get()
    saved_receipt = application.encrypted_receipt
    application.encrypted_receipt = "Synthetic damaged reconciliation audit"
    application.save(update_fields=["encrypted_receipt"])
    with pytest.raises(CommandError):
        call_command("clear_recovery_sessions", **session_arguments)
    assert Session.objects.count() == session_count
    application.encrypted_receipt = saved_receipt
    application.save(update_fields=["encrypted_receipt"])
    sessions_output = StringIO()
    call_command("clear_recovery_sessions", stdout=sessions_output, **session_arguments)
    assert json.loads(sessions_output.getvalue()) == {
        "sessions_deleted": session_count,
        "publication_authorized": False,
    }
    assert not Session.objects.exists()
    sessions_output = StringIO()
    call_command("clear_recovery_sessions", stdout=sessions_output, **session_arguments)
    assert json.loads(sessions_output.getvalue())["sessions_deleted"] == 0
    output = StringIO()
    call_command("apply_recovery_ledger", stdout=output, **arguments)
    assert json.loads(output.getvalue())["applied"] == 0
    assert RecoveryApplication.objects.count() == RecoveryMediaJob.objects.count() == 1

    # A bad restored cache root must keep recovery closed and emit no partial result.
    cache_root = settings.RIGHTS_DELIVERY_ROOT
    shared_link = tmp_path / 'invalid-delivery-link'
    shared_link.symlink_to(cache_root, target_is_directory=True)
    settings.RIGHTS_DELIVERY_ROOT = shared_link
    rejected_output = StringIO()
    with pytest.raises(CommandError, match='keep isolated'):
        call_command('apply_recovery_ledger', stdout=rejected_output, **arguments)
    assert rejected_output.getvalue() == '' and settings.RECOVERY_MODE
    settings.RIGHTS_DELIVERY_ROOT = cache_root
    retry_output = StringIO()
    call_command('apply_recovery_ledger', stdout=retry_output, **arguments)
    assert json.loads(retry_output.getvalue())['applied'] == 0
