"""Persist stable signed records. This does not publish an external checkpoint."""

from django.db import connection, transaction
from django.views.decorators.debug import sensitive_variables

from scripts.recovery_ledger import ZERO, Checkpoint, LedgerIntegrityError

from .crypto import unseal
from .models import RecoveryLedgerState, RecoveryOutbox


@transaction.atomic
@sensitive_variables()
def prepare_batch(codec, limit=100):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Batch limit must be between 1 and 100")
    # Serialize initialization and all producers on PostgreSQL, including empty state.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [82940099])
    state, _ = RecoveryLedgerState.objects.get_or_create(pk=1)
    state = RecoveryLedgerState.objects.select_for_update().get(pk=1)
    checkpoint = Checkpoint(str(state.ledger_id), state.sequence, state.head)
    existing = list(
        RecoveryOutbox.objects.select_for_update()
        .filter(sequence__isnull=False)
        .order_by("sequence")
    )
    if RecoveryOutbox.objects.filter(sequence__isnull=True, encoded_record__isnull=False).exists():
        raise LedgerIntegrityError("Incomplete producer metadata")
    records = [event.encoded_record for event in existing]
    payloads = codec.verify(records, Checkpoint(checkpoint.ledger, 0, ZERO), checkpoint)
    for event, record, payload in zip(existing, records, payloads, strict=True):
        if (
            record["event"] != str(event.event_id)
            or record["sequence"] != event.sequence
            or payload != unseal(event.encrypted_event)
        ):
            raise LedgerIntegrityError("Outbox binding changed")
        if payload.get("execution") != str(event.execution_id):
            raise LedgerIntegrityError("Execution binding changed")
    pending = list(
        RecoveryOutbox.objects.select_for_update()
        .filter(sequence__isnull=True)
        .order_by("pk")[:limit]
    )
    for event in pending:
        payload = unseal(event.encrypted_event)
        if not isinstance(payload, dict) or payload.get("execution") != str(event.execution_id):
            raise LedgerIntegrityError("Execution binding changed")
        record, checkpoint = codec.append(checkpoint, str(event.event_id), payload)
        records.append(record)
        codec.verify(records, Checkpoint(checkpoint.ledger, 0, ZERO), checkpoint)
        event.sequence = checkpoint.sequence
        event.encoded_record = record
        event.save(update_fields=["sequence", "encoded_record"])
        # exported_at remains null until an independent adapter confirms durability.
    state.sequence, state.head = checkpoint.sequence, checkpoint.head
    state.save(update_fields=["sequence", "head"])
    return checkpoint, list(
        RecoveryOutbox.objects.filter(exported_at__isnull=True, sequence__isnull=False)
        .order_by("sequence")
        .values_list("encoded_record", flat=True)[:limit]
    )
