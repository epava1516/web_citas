"""Native PostgreSQL pipeline equivalence, isolation and savepoint recovery."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from decimal import Decimal
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connection, connections, transaction
from django.utils import timezone
from psycopg.types.json import Jsonb
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_validation_seal import check, full_rejects, generated

from apps.core.models import User
from apps.safety import rights_validation_seal as seals
from apps.safety.crypto import seal, unseal
from apps.safety.models import RightsExportValidationSeal

pytestmark = pytest.mark.django_db(transaction=True)


def native_pipeline():
    connection.ensure_connection()
    raw = seals._pipeline_connection()
    assert raw is not None, "This PostgreSQL gate requires actual supported psycopg pipeline"
    return raw


def test_native_pipeline_matches_ordered_typed_and_empty_hashes():
    values = [
        (
            "SELECT %s::uuid AS id, %s::numeric AS amount, %s::jsonb AS facts",
            [uuid4(), Decimal("1.2300"), Jsonb({"unicode": "á", "rows": [1, None]})],
        ),
        (
            "SELECT %s::timestamptz AS expires_at",
            [datetime(2030, 1, 2, tzinfo=datetime_timezone.utc)],
        ),
        ("SELECT value FROM unnest(%s::integer[]) AS value ORDER BY value DESC", [[1, 3, 2]]),
        ("SELECT 1 AS empty WHERE FALSE", None),
    ] * 5
    with transaction.atomic():
        raw = native_pipeline()
        expected = seals._replay_serial(values)
        assert seals._replay_pipeline(values, raw) == expected
        assert seals._replay(values) == expected
        assert raw._pipeline is None


@pytest.mark.parametrize("position", [0, 4, 9])
def test_pipeline_sql_failure_drains_before_savepoint_rollback_and_outer_query(position):
    statements = [("SELECT %s::integer AS value", [index]) for index in range(10)]
    statements[position] = ("SELECT nonexistent_column_mod08 FROM pg_catalog.pg_class", None)
    with transaction.atomic():
        raw = native_pipeline()
        with pytest.raises(DatabaseError):
            with transaction.atomic():
                seals._replay(statements)
        assert raw._pipeline is None
        with connection.cursor() as cursor:
            cursor.execute("SELECT 42")
            assert cursor.fetchone() == (42,)
        assert seals._replay([("SELECT 7 AS value", None)]) == seals._replay_serial(
            [("SELECT 7 AS value", None)]
        )


def test_pipeline_keeps_read_committed_statement_snapshots_after_real_lock_wait(request, settings):
    request.getfixturevalue("directory")
    users = list(User.objects.order_by("pk")[:2])
    assert len(users) == 2
    pids = Queue()
    statements = [
        ("SELECT id, first_name FROM core_user WHERE id=%s FOR UPDATE", [users[0].pk]),
        ("SELECT id, first_name FROM core_user WHERE id=%s", [users[1].pk]),
    ]

    def reader():
        connections.close_all()
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout='8s'")
                cursor.execute("SET LOCAL statement_timeout='12s'")
                cursor.execute("SHOW transaction_isolation")
                assert cursor.fetchone()[0] == "read committed"
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
                native_pipeline()
                return seals._replay(statements)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(), connection.cursor() as cursor:
            User.objects.select_for_update().get(pk=users[0].pk)
            cursor.execute("SELECT pg_backend_pid()")
            holder = cursor.fetchone()[0]
            future = pool.submit(reader)
            observe_blocked(pids.get(timeout=5), holder)
            User.objects.filter(pk=users[1].pk).update(
                first_name="Committed while first statement waited"
            )
        observed = future.result(timeout=15)
    with transaction.atomic():
        assert observed == seals._replay_serial(statements)


def test_pipeline_pending_cursor_limit_and_failure_closes_every_cursor(monkeypatch):
    from contextlib import contextmanager

    opened, closed, live = [], [], set()
    native_cursor = connection.cursor

    @contextmanager
    def tracked():
        with native_cursor() as cursor:
            opened.append(cursor)
            live.add(id(cursor))
            assert len(live) <= 8
            try:
                yield cursor
            finally:
                live.remove(id(cursor))
                closed.append(cursor)

    with transaction.atomic():
        raw = native_pipeline()
        monkeypatch.setattr(connection, "cursor", tracked)
        statements = [("SELECT %s::integer AS value", [index]) for index in range(19)]
        assert len(seals._replay(statements)) == 19
        assert len(opened) == len(closed) == 19 and not live
        with pytest.raises(DatabaseError):
            with transaction.atomic():
                seals._replay([("SELECT 1 AS value", None), ("SELECT mod08_missing_column", None)])
        assert len(opened) == len(closed) and not live
        assert raw._pipeline is None


def test_unsupported_pipeline_uses_actual_serial_postgresql(monkeypatch):
    with transaction.atomic():
        monkeypatch.setattr(seals, "_pipeline_connection", lambda: None)
        values = [("SELECT 9 AS value", None)]
        assert seals._replay(values) == seals._replay_serial(values)


@pytest.mark.parametrize("change", ["session", "ciphertext", "source"])
def test_pipeline_never_bypasses_original_full_fresh_guards(request, settings, monkeypatch, change):
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)
    assert check(case, author, export) is True
    if change == "session":
        User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
    elif change == "ciphertext":
        image = export.images.get()
        image.encrypted_content = "damaged"
        image.save(update_fields=["encrypted_content"])
    else:
        person = case.person
        person.alias = "Changed original source alias after first validation"
        person.save(update_fields=["alias"])
    if change != "session":
        assert full_rejects(case, author, export) is True
    with pytest.raises((PermissionDenied, ValidationError)):
        check(case, author, export)


def test_expired_seal_falls_back_to_real_full_validation(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)
    RightsExportValidationSeal.objects.filter(export=export).update(
        valid_until=timezone.now() - timedelta(seconds=1)
    )
    assert check(case, author, export) is False


def test_invalid_replayed_sql_falls_back_to_real_full_validation(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)
    assert check(case, author, export) is True
    candidate = RightsExportValidationSeal.objects.filter(export=export).latest("pk")
    statement = unseal(candidate.encrypted_statements)
    statement["statements"].insert(
        1, ["SELECT missing_mod08_column FROM pg_catalog.pg_class", None]
    )
    candidate.encrypted_statements = seal(statement)
    candidate.save(update_fields=["encrypted_statements"])
    assert check(case, author, export) is False
    assert connection.connection._pipeline is None
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)


def test_existing_native_pipeline_is_not_nested_and_remains_operational():
    values = [("SELECT %s::integer AS value", [index]) for index in range(3)]
    with transaction.atomic():
        raw = native_pipeline()
        expected = seals._replay_serial(values)
        with raw.pipeline() as owner:
            assert seals._pipeline_connection() is None
            assert seals._replay(values) == expected
            assert raw._pipeline is owner
            with connection.cursor() as cursor:
                cursor.execute("SELECT 31")
                owner.sync()
                assert cursor.fetchone() == (31,)
        assert raw._pipeline is None


def test_recording_keeps_serial_replay_and_identical_state_digests():
    values = [("SELECT %s::integer AS value", [index]) for index in range(3)]
    with transaction.atomic():
        raw = native_pipeline()
        with seals.recording() as serial_state:
            expected = seals._replay_serial(values)
        with seals.recording() as dispatched_state:
            assert seals._pipeline_connection() is None
            actual = seals._replay(values)
        assert actual == expected
        assert dispatched_state == serial_state
        assert dispatched_state["supported"]
        assert len(dispatched_state["digests"]) == 3
        assert raw._pipeline is None


def test_seal_expiry_after_real_pipeline_replay_forces_fresh_full_fallback(
    request, settings, monkeypatch
):
    # Controlled temporal unit boundary around REAL PG replay. No sleep or
    # provider verification is simulated; original domain expiries stay intact.
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)
    assert check(case, author, export) is True
    start = timezone.now()
    until = start + timedelta(seconds=1)
    RightsExportValidationSeal.objects.filter(export=export).update(valid_until=until)
    clock, calls = [start], []
    native = seals._replay

    def replayed(*args, **kwargs):
        result = native(*args, **kwargs)
        calls.append(True)
        clock[0] = until + timedelta(microseconds=1)
        return result

    monkeypatch.setattr(seals.timezone, "now", lambda: clock[0])
    monkeypatch.setattr(seals, "_replay", replayed)
    assert check(case, author, export) is False
    assert calls == [True]
    assert connection.connection._pipeline is None
    # Full validation created a new seal bounded by the untouched originals.
    assert RightsExportValidationSeal.objects.filter(
        export=export, valid_until__gt=clock[0]
    ).exists()
