"""Owned PostgreSQL cleanup must wait for clients without terminating them."""

from uuid import uuid4

import psycopg
import pytest
from capacity_runtime_role import _owned_database
from directory_snapshot import SnapshotBusy, _admin
from psycopg import sql
from test_capacity_chain_inline_http import await_clone_quiescent

pytestmark = pytest.mark.django_db(transaction=True)


def test_clone_cleanup_preserves_live_connection_and_accepts_closed_connection():
    database = dict(_owned_database())
    target = "chain_cleanup_" + uuid4().hex
    with _admin(database) as admin, admin.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target))
        )
        try:
            with psycopg.connect(
                dbname=target,
                user=database["USER"],
                password=database["PASSWORD"],
                host=database["HOST"],
                port=database["PORT"],
                autocommit=True,
            ) as client:
                with pytest.raises(SnapshotBusy, match="live connections"):
                    await_clone_quiescent(cursor, target, timeout=0.05)
                # A timed-out cleanup must not terminate the client's backend.
                assert client.execute("SELECT current_database()").fetchone() == (target,)
            await_clone_quiescent(cursor, target)
        finally:
            # Never use FORCE or pg_terminate_backend to make cleanup appear valid.
            await_clone_quiescent(cursor, target)
            cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(target)))
