# ruff: noqa: F811 -- imported fixtures are requested by parameter name
"""Real PostgreSQL transport equivalence; timing is diagnostic, not acceptance."""

import json
import resource
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from statistics import median
from threading import Event
from time import monotonic, perf_counter_ns
from uuid import uuid4

import psycopg
import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, close_old_connections, connection, transaction
from psycopg import sql
from test_rights_evidence_chain import base, runtime, set_role  # noqa: F401

from apps.safety import evidence_chain as chain
from apps.safety import rights_validation_seal as seal
from apps.safety.evidence_chain_sql_v1 import TABLES

pytestmark = pytest.mark.django_db(transaction=True)


def test_autocommit_validation_keeps_head_lock_until_source_validation(base, monkeypatch):
    case = base[0]
    assert not connection.in_atomic_block
    original = chain._source_rows
    admin = psycopg.connect(**connection.get_connection_params(), autocommit=True)

    def inspect_locked_source(request):
        assert connection.in_atomic_block
        # Another transaction cannot lock the head while validation is still
        # comparing the current source rows. NOWAIT makes this assertion finite.
        with pytest.raises(psycopg.errors.LockNotAvailable):
            admin.execute("SELECT request_id FROM public.safety_rightsevidencehead "
                          "WHERE request_id=%s FOR UPDATE NOWAIT", [case.pk])
        return original(request)

    monkeypatch.setattr(chain, "_source_rows", inspect_locked_source)
    try:
        assert chain.validate_chain(case).count == 7
        assert not connection.in_atomic_block
        assert admin.execute("SELECT request_id FROM public.safety_rightsevidencehead "
                             "WHERE request_id=%s FOR UPDATE NOWAIT", [case.pk]).fetchone()
    finally:
        admin.close()


def test_same_seven_queries_rows_and_ticket(base, runtime):
    case = base[0]
    assert connection.vendor == "postgresql" and connection.pg_version // 10000 == 17
    expected_ticket = chain.validate_chain(case)
    set_role(runtime)
    statements = chain._source_statements(str(case.pk))
    assert len(statements) == len(TABLES) == 7
    with transaction.atomic():
        original = chain._source_rows_serial(statements)
        assert chain._source_rows_pipeline(statements, connection.connection) == original
        assert len(original) == 7
        assert chain.validate_chain(case) == expected_ticket


@pytest.mark.parametrize("position", [0, 6])
def test_first_and_last_corruption_rejected_in_both_paths(base, monkeypatch, position):
    case, _, _, _, rows = base
    type(rows[position]).objects.filter(pk=rows[position].pk).update(source_digest="0" * 64)
    for pipeline in (False, True):
        with monkeypatch.context() as patch:
            if not pipeline:
                patch.setattr(seal, "_pipeline_connection", lambda: None)
            with pytest.raises(ValidationError, match="source rows"), transaction.atomic():
                chain.validate_chain(case)


@pytest.mark.parametrize("position", [0, 6])
def test_sql_first_error_drain_and_savepoint_connection_reuse(base, position):
    statements = chain._source_statements(str(base[0].pk))
    statements[position] = ("SELECT 1/0", None)
    if position == 0:
        statements[1] = ("SELECT mod08_missing_column", None)
    codes = []
    with transaction.atomic():
        for pipeline in (False, True):
            with pytest.raises(DatabaseError) as captured, transaction.atomic():
                if pipeline:
                    chain._source_rows_pipeline(statements, connection.connection)
                else:
                    chain._source_rows_serial(statements)
            codes.append(captured.value.__cause__.sqlstate)
            with connection.cursor() as cursor:
                cursor.execute("SELECT 42")
                assert cursor.fetchone() == (42,)
            assert connection.connection._pipeline is None
    assert codes == ["22012", "22012"]


def test_recorder_falls_back_and_preserves_all_seven_results(base, monkeypatch):
    def unexpected(*args):
        raise AssertionError("recorder must retain serial capture")

    monkeypatch.setattr(chain, "_source_rows_pipeline", unexpected)
    with transaction.atomic(), seal.recording() as captured:
        actual = chain._source_rows(str(base[0].pk))
    assert len(actual) == 7
    assert captured["supported"]
    assert len(captured["statements"]) == len(captured["digests"]) == 7
    assert seal._replay_serial(captured["statements"]) == captured["digests"]


@pytest.mark.parametrize("reason", ["nested", "vendor", "support"])
def test_real_serial_fallback(base, monkeypatch, reason):
    def unexpected(*args):
        raise AssertionError("unsupported context must use serial path")

    monkeypatch.setattr(chain, "_source_rows_pipeline", unexpected)
    with transaction.atomic():
        if reason == "nested":
            with connection.connection.pipeline():
                assert len(chain._source_rows(str(base[0].pk))) == 7
        else:
            if reason == "vendor":
                monkeypatch.setattr(connection, "vendor", "unsupported")
            else:
                monkeypatch.setattr(psycopg.Pipeline, "is_supported", staticmethod(lambda: False))
            assert len(chain._source_rows(str(base[0].pk))) == 7


@pytest.mark.parametrize("pipeline", [False, True])
def test_committed_change_between_queries_visible_in_later_snapshot(base, runtime, monkeypatch, pipeline):
    case, _, _, _, rows = base
    statements = chain._source_statements(str(case.pk))
    original = chain._source_rows_serial(statements)
    key = int(uuid4().hex[:12], 16)
    query, params = statements[1]
    statements[1] = (
        "WITH barrier AS MATERIALIZED (SELECT pg_advisory_xact_lock(%s)) "
        f"SELECT q.* FROM barrier CROSS JOIN ({query}) q", [key, *params],
    )
    admin = psycopg.connect(**connection.get_connection_params(), autocommit=True)
    admin.execute("SELECT pg_advisory_lock(%s)", [key])
    started, pid = Event(), []

    def consume():
        close_old_connections()
        try:
            set_role(runtime)
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL statement_timeout='15s'")
                    cursor.execute("SELECT pg_backend_pid()")
                    pid.append(cursor.fetchone()[0])
                started.set()
                return (chain._source_rows_pipeline(statements, connection.connection) if pipeline
                        else chain._source_rows_serial(statements))
        finally:
            connection.close()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(consume)
            assert started.wait(10)
            deadline = monotonic() + 10
            while True:
                waiting = admin.execute("SELECT wait_event FROM pg_stat_activity WHERE pid=%s", pid).fetchone()
                if waiting and waiting[0] == "advisory":
                    break
                assert monotonic() < deadline, "bounded query barrier was not reached"
                Event().wait(0.01)
            # Source row is in the LAST table, not the query already waiting.
            # Owner mutation bypasses the immutable guard solely to simulate drift.
            admin.execute(sql.SQL("ALTER TABLE public.{} DISABLE TRIGGER rights_evidence_no_modify").format(
                sql.Identifier(TABLES[-1])))
            admin.execute(sql.SQL("UPDATE public.{} SET source_digest=%s WHERE id=%s").format(
                sql.Identifier(TABLES[-1])), ["0" * 64, rows[-1].pk])
            admin.execute(sql.SQL("ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_no_modify").format(
                sql.Identifier(TABLES[-1])))
            admin.execute("SELECT pg_advisory_unlock(%s)", [key])
            actual = future.result(timeout=20)
        last = (TABLES[-1], str(rows[-1].pk))
        assert actual[last] != original[last]
        assert {key: value for key, value in actual.items() if key != last} == {
            key: value for key, value in original.items() if key != last
        }
        with pytest.raises(ValidationError, match="source rows"):
            chain.validate_chain(case)
    finally:
        admin.execute("SELECT pg_advisory_unlock(%s)", [key])
        admin.execute(sql.SQL("ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_no_modify").format(
            sql.Identifier(TABLES[-1])))
        admin.close()


def test_alternating_source_transport_measurement(base, runtime, record_property):
    set_role(runtime)
    statements = chain._source_statements(str(base[0].pk))
    samples = {"serial": [], "pipeline": []}
    results = {}
    for iteration in range(22):
        order = ("serial", "pipeline") if iteration % 2 == 0 else ("pipeline", "serial")
        for variant in order:
            with transaction.atomic():
                started = perf_counter_ns()
                actual = (chain._source_rows_serial(statements) if variant == "serial"
                          else chain._source_rows_pipeline(statements, connection.connection))
                elapsed = perf_counter_ns() - started
            results[variant] = actual
            if iteration >= 2:
                samples[variant].append(elapsed)
        assert results["serial"] == results["pipeline"]
    memory = {}
    assert not tracemalloc.is_tracing(), "memory diagnostic must not reset another collector"
    for variant in ("serial", "pipeline"):
        tracemalloc.start()
        try:
            with transaction.atomic():
                if variant == "serial":
                    measured = chain._source_rows_serial(statements)
                else:
                    measured = chain._source_rows_pipeline(statements, connection.connection)
            assert measured == results[variant]
            _, peak = tracemalloc.get_traced_memory()
            memory[variant] = {"python_traced_peak_bytes": peak,
                               "process_lifetime_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        finally:
            tracemalloc.stop()
    record_property("chain_source_pipeline_diagnostic", json.dumps({
        "status": "DIAGNOSTIC_NOT_ACCEPTANCE", "rows": len(results["serial"]),
        "result_payload_utf8_bytes": sum(len(key[0]) + len(key[1]) + len(value)
                                         for key, value in results["serial"].items()),
        "memory_limit_verified": False,
        "memory": memory,
        "memory_caveat": "traced peak excludes libpq; maxrss is process lifetime, not per-operation",
        "metrics": {name: {"count": len(values), "median_ns": median(values), "samples_ns": values}
                    for name, values in samples.items()},
    }, sort_keys=True))
