from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.db import transaction
from test_account_erasure_execution import prepared_erasure
from test_erasure_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryLedgerState, RecoveryOutbox
from apps.safety.recovery_ledger_export import export_batch
from apps.safety.recovery_ledger_producer import prepare_batch
from scripts.recovery_ledger import ZERO, Checkpoint, LedgerIntegrityError, RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def test_committed_file_survives_db_failure_and_retry_confirms_it(
    request, settings, monkeypatch, tmp_path
):
    case, actor, staff, subject, public, receipt, plan, purposes, stored, acceptance = (
        prepared_erasure(request, settings, monkeypatch, agency=True)
    )
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    codec = RecoveryLedger(Fernet.generate_key(), b"e" * 32)
    state, records = prepare_batch(codec)
    records_dir, authority_dir = tmp_path / "records", tmp_path / "authority"
    records_dir.mkdir(mode=0o700)
    authority_dir.mkdir(mode=0o700)
    store = RecoveryStore(records_dir, authority_dir, codec)
    start = Checkpoint(state.ledger, 0, ZERO)
    with pytest.raises(LedgerIntegrityError):
        export_batch(store)
    assert RecoveryOutbox.objects.get(execution=execution).exported_at is None
    store.initialize(start)
    original_save = RecoveryOutbox.save

    def fail_ack(self, *args, **kwargs):
        if kwargs.get("update_fields") == ["exported_at"]:
            raise RuntimeError("Synthetic DB acknowledgement failure")
        return original_save(self, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(RecoveryOutbox, "save", fail_ack)
        with pytest.raises(RuntimeError):
            export_batch(store)
    assert store.checkpoint() == state
    event = RecoveryOutbox.objects.get(execution=execution)
    assert event.exported_at is None
    from scripts.recovery_receipts import validate_receipt

    assert validate_receipt(store.recover(start)[0])["execution"] == str(execution.pk)
    assert export_batch(store) == 1
    event.refresh_from_db()
    assert event.exported_at is not None and event.encoded_record == records[0]
    assert export_batch(store) == 0
    assert len(list(records_dir.glob("*.json"))) == 1
    with transaction.atomic(), pytest.raises(RuntimeError):
        export_batch(store)
    # A business backup rolled back behind the independent checkpoint cannot export.
    RecoveryOutbox.objects.filter(pk=event.pk).update(
        sequence=None, encoded_record=None, exported_at=None
    )
    RecoveryLedgerState.objects.update(sequence=0, head=ZERO)
    # Producer would create a fresh randomized record with the same sequence;
    # its head differs from the already checkpointed artifact and must be rejected.
    with pytest.raises(LedgerIntegrityError):
        export_batch(store)
    assert store.checkpoint() == state


def test_actual_media_receipt_passes_typed_validation(request, settings, monkeypatch):
    from test_erasure_execution import payload
    from test_media_erasure import setup

    from apps.safety.crypto import unseal
    from scripts.recovery_receipts import validate_receipt

    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = RecoveryOutbox.objects.get(execution=execution)
    assert validate_receipt(unseal(event.encrypted_event))["references"]["media_jobs"]
