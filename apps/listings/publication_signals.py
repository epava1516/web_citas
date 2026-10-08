"""Queue a stored-state refresh after transactions that wrote rule dependencies.

Only a latency optimization: database triggers already marked the affected listings,
reads evaluate them natively meanwhile, and Beat retries anything the queue missed
(bulk writes and raw SQL do not send model signals).
"""

from django.db import connection, transaction

from .publication_state import DEPENDENCY_TABLES


def schedule_refresh(sender, **kwargs):
    model = kwargs.get("through") if "through" in kwargs else sender
    if model is None or model._meta.db_table not in DEPENDENCY_TABLES:
        return
    if getattr(connection, "_publication_refresh_scheduled", False):
        return
    connection._publication_refresh_scheduled = True

    def enqueue():
        connection._publication_refresh_scheduled = False
        from .tasks import refresh_publication_state

        refresh_publication_state.delay()

    transaction.on_commit(enqueue, robust=True)
