"""Local durable export; file writes survive transaction rollback by design."""

from django.db import connection, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from scripts.recovery_ledger import LedgerIntegrityError

from .models import RecoveryOutbox
from .recovery_ledger_producer import prepare_batch


@sensitive_variables()
def export_batch(store, limit=100):
    if connection.in_atomic_block:
        raise RuntimeError("Exporter requires committed producer transactions")
    state, _ = prepare_batch(store.codec, limit)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [82940100])
        external = store.checkpoint()
        if external.ledger != state.ledger or external.sequence > state.sequence:
            raise LedgerIntegrityError("Restored or mismatched business ledger; reconcile first")
        if external.sequence == state.sequence and external.head != state.head:
            raise LedgerIntegrityError("Checkpoint head mismatch")
        events = list(
            RecoveryOutbox.objects.select_for_update()
            .filter(exported_at__isnull=True, sequence__isnull=False)
            .order_by("sequence")[:limit]
        )
        for event in events:
            current = store.checkpoint()
            if event.sequence <= current.sequence:
                store.confirm(event.encoded_record)
            else:
                store.append(event.encoded_record)
            event.exported_at = timezone.now()
            event.save(update_fields=["exported_at"])
        return len(events)
