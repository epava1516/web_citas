from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.db import close_old_connections, connections
from test_account_erasure_execution import prepared_erasure
from test_erasure_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryLedgerState, RecoveryOutbox
from apps.safety.recovery_ledger_producer import prepare_batch
from scripts.recovery_ledger import LedgerIntegrityError, RecoveryLedger

pytestmark = pytest.mark.django_db(transaction=True)


def test_concurrent_producer_replay_and_tamper_rollback(request, settings, monkeypatch):
    case, actor, staff, subject, public, receipt, plan, purposes, stored, acceptance = (
        prepared_erasure(request, settings, monkeypatch, agency=True)
    )
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    codec = RecoveryLedger(Fernet.generate_key(), b"p" * 32)

    def worker():
        close_old_connections()
        try:
            return prepare_batch(codec)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        results = [future.result(timeout=30) for future in futures]
    assert results[0] == results[1]
    checkpoint, records = results[0]
    assert checkpoint.sequence == 1 and len(records) == 1
    event = RecoveryOutbox.objects.get(execution=execution)
    assert event.sequence == 1 and event.encoded_record == records[0]
    assert event.exported_at is None
    assert prepare_batch(codec) == results[0]
    with pytest.raises(LedgerIntegrityError):
        prepare_batch(RecoveryLedger(Fernet.generate_key(), b"q" * 32))
    state = RecoveryLedgerState.objects.get()
    assert state.sequence == 1 and state.head == checkpoint.head
    damaged = dict(event.encoded_record) | {"previous": "0" * 63 + "1"}
    RecoveryOutbox.objects.filter(pk=event.pk).update(encoded_record=damaged)
    with pytest.raises(LedgerIntegrityError):
        prepare_batch(codec)
    state.refresh_from_db()
    assert state.sequence == 1 and state.head == checkpoint.head
    RecoveryOutbox.objects.filter(pk=event.pk).update(encoded_record=records[0])
    assert prepare_batch(codec) == results[0]
