"""Temporary browser ORM threads must release their real PostgreSQL connections."""

import pytest
from django.db import connection
from test_reset_localization import db_sync


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation_fails", [False, True])
def test_temporary_browser_orm_thread_closes_connection(monkeypatch, operation_fails):
    assert connection.vendor == "postgresql"
    # A healthy persistent connection must still close when its owner thread ends.
    monkeypatch.setitem(connection.settings_dict, "CONN_MAX_AGE", 60)
    observed = []

    def operation():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            backend = cursor.fetchone()[0]
        # Retain the actual driver object: GC must not implement thread cleanup.
        observed.append((connection.connection, backend))
        if operation_fails:
            raise ValueError("Synthetic browser ORM operation failure")
        return backend

    try:
        if operation_fails:
            with pytest.raises(ValueError, match="Synthetic browser ORM operation failure"):
                db_sync(operation)
        else:
            assert db_sync(operation) == observed[0][1]
        assert len(observed) == 1
        assert observed[0][0].closed, "Retiring ORM thread left its PostgreSQL connection open"
    finally:
        # Preserve service hygiene even when testing the defective helper.
        for driver, _ in observed:
            driver.close()
