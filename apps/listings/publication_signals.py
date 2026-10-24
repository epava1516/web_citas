"""Queue a stored-state refresh after transactions that wrote rule dependencies.

Only a latency optimization: database triggers already marked the affected listings,
reads evaluate them natively meanwhile, and Beat retries anything the queue missed
(bulk writes and raw SQL do not send model signals).
"""

from django.apps import apps
from django.db import connection, transaction

from .publication_state import DEPENDENCY_TABLES


def _enqueue_refresh():
    from .tasks import refresh_publication_state

    refresh_publication_state.delay()


def schedule_refresh(sender, **kwargs):
    model = kwargs.get("through") if "through" in kwargs else sender
    if model is None or model._meta.db_table not in DEPENDENCY_TABLES:
        return
    # Historical migration models cannot dispatch a current-schema worker.
    # Database invalidation, native reads and Beat remain authoritative.
    if model._meta.apps is not apps:
        return
    # Django removes pending callbacks on transaction/savepoint rollback.
    # Deduplicate against that queue, so discarded work cannot leave a sticky
    # connection flag that suppresses refreshes in later transactions.
    if any(callback is _enqueue_refresh for _, callback, _ in connection.run_on_commit):
        return
    transaction.on_commit(_enqueue_refresh, robust=True)
