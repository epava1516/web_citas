# ruff: noqa: F811 -- imported fixtures are requested by parameter name
"""Finite PostgreSQL experiment; measurements are diagnostic, never acceptance."""

import json
from concurrent.futures import ThreadPoolExecutor
from statistics import median
from threading import Event
from time import monotonic, perf_counter_ns
from uuid import uuid4

import psycopg
import pytest
from capacity_runtime_sql_probe import attest, install, probe, reference
from django.db import connection, transaction
from psycopg import sql
from test_rights_evidence_chain import base, runtime, set_role  # noqa: F401

from apps.safety.evidence_chain_sql_v1 import TABLES
from apps.safety.rights_validation_seal import _replay_serial, recording

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def helper(base, runtime):
    assert connection.vendor == "postgresql"
    assert connection.pg_version // 10000 == 17
    name = "mod08_probe_" + uuid4().hex
    with connection.cursor() as cursor:
        expected = install(cursor, name)
        cursor.execute(sql.SQL("REVOKE ALL ON FUNCTION public.{}() FROM PUBLIC").format(sql.Identifier(name)))
        cursor.execute(sql.SQL("GRANT EXECUTE ON FUNCTION public.{}() TO {}").format(
            sql.Identifier(name), sql.Identifier(runtime)))
    try:
        yield name, expected
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("DROP FUNCTION public.{}()").format(sql.Identifier(name)))


def test_reference_trace_and_attested_helper_match(helper, runtime):
    name, expected = helper
    set_role(runtime)
    with connection.cursor() as cursor:
        original = reference(cursor)
        assert original["trusted"] is True
        assert len(original["stages"]) == 9
        assert probe(cursor, name, expected) == original


def test_owner_and_altered_attributes_are_rejected(helper, runtime):
    name, expected = helper
    with connection.cursor() as cursor:
        with pytest.raises(ValueError, match="attestation"):
            attest(cursor, name, expected)
        cursor.execute(sql.SQL("ALTER FUNCTION public.{}() STABLE").format(sql.Identifier(name)))
    set_role(runtime)
    with connection.cursor() as cursor, pytest.raises(ValueError, match="attestation"):
        probe(cursor, name, expected)


def test_granted_update_short_circuit_preserves_original_rows(helper, runtime):
    name, expected = helper
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("GRANT UPDATE ON public.{} TO {}").format(
            sql.Identifier(TABLES[0]), sql.Identifier(runtime)))
    try:
        set_role(runtime)
        with connection.cursor() as cursor:
            original = reference(cursor)
            assert original["trusted"] is False
            assert len(original["stages"]) == 3
            assert probe(cursor, name, expected) == original
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("REVOKE UPDATE ON public.{} FROM {}").format(
                sql.Identifier(TABLES[0]), sql.Identifier(runtime)))


def test_true_to_true_trace_change_invalidates_recorded_result(helper, runtime):
    name, expected = helper
    set_role(runtime)
    with transaction.atomic(), recording() as captured, connection.cursor() as cursor:
        before = probe(cursor, name, expected)
    assert captured["supported"]
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
        cursor.execute(sql.SQL("CREATE TRIGGER mod08_probe_extra BEFORE INSERT ON public.{} "
                               "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_guard()").format(
                                   sql.Identifier(TABLES[0])))
    try:
        set_role(runtime)
        with connection.cursor() as cursor:
            after = probe(cursor, name, expected)
        assert before["trusted"] is after["trusted"] is True
        assert before["stages"] != after["stages"]
        assert _replay_serial(captured["statements"]) != captured["digests"]
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("DROP TRIGGER mod08_probe_extra ON public.{}").format(sql.Identifier(TABLES[0])))


def test_volatile_internal_query_observes_concurrent_grant(base, runtime):
    name = "mod08_probe_" + uuid4().hex
    key = int(uuid4().hex[:12], 16)
    params = connection.get_connection_params().copy()
    admin = psycopg.connect(**params, autocommit=True)
    started = Event()
    pid = []
    with connection.cursor() as cursor:
        expected = install(cursor, name, pause_stage=2, pause_key=key)
    admin.execute("SELECT pg_advisory_lock(%s)", [key])

    def consume():
        with psycopg.connect(**params) as db:
            db.execute("SET statement_timeout = '15s'")
            db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(runtime)))
            pid.append(db.info.backend_pid)
            started.set()
            with db.cursor() as cursor:
                return probe(cursor, name, expected)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(consume)
            assert started.wait(10)
            deadline = monotonic() + 10
            while True:
                waiting = admin.execute("SELECT wait_event FROM pg_stat_activity WHERE pid=%s", pid).fetchone()
                if waiting and waiting[0] == "advisory":
                    break
                assert monotonic() < deadline, "helper did not reach bounded synchronization"
                # Event wait yields the controller; condition, not elapsed time,
                # determines when the concurrent mutation is issued.
                Event().wait(0.01)
            admin.execute(sql.SQL("GRANT UPDATE ON public.{} TO {}").format(
                sql.Identifier(TABLES[0]), sql.Identifier(runtime)))
            admin.execute("SELECT pg_advisory_unlock(%s)", [key])
            observed = future.result(timeout=15)
        assert observed["trusted"] is False
        assert len(observed["stages"]) == 3
    finally:
        admin.execute("SELECT pg_advisory_unlock(%s)", [key])
        admin.execute(sql.SQL("REVOKE UPDATE ON public.{} FROM {}").format(
            sql.Identifier(TABLES[0]), sql.Identifier(runtime)))
        admin.execute(sql.SQL("DROP FUNCTION public.{}()").format(sql.Identifier(name)))
        admin.close()


def test_attestation_execute_race_is_a_production_rejection(helper, runtime, record_property):
    """A correct trace does not close independent attestation's TOCTOU window."""
    name, expected = helper
    admin = psycopg.connect(**connection.get_connection_params(), autocommit=True)
    set_role(runtime)
    forged = {"trusted": True, "stages": []}

    class RacingCursor:
        def __init__(self, raw):
            self.raw = raw
            self.executions = 0

        def execute(self, statement, params=None):
            self.executions += 1
            if self.executions == 2:
                admin.execute(sql.SQL("CREATE OR REPLACE FUNCTION public.{}() RETURNS jsonb "
                    "LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE "
                    "SET search_path=pg_catalog,pg_temp AS $race$ BEGIN "
                    "RETURN '{{\"trusted\":true,\"stages\":[]}}'::jsonb; END $race$").format(
                        sql.Identifier(name)))
            self.raw.execute(statement, params)

        def fetchone(self):
            return self.raw.fetchone()

    try:
        with connection.cursor() as cursor:
            assert probe(RacingCursor(cursor), name, expected) == forged
        record_property("runtime_sql_probe_security", json.dumps({
            "status": "REJECTED_FOR_PRODUCTION", "reason": "attestation_execution_toctou",
            "replacement_observed": True,
        }, sort_keys=True))
    finally:
        admin.close()


def test_recorder_and_replay_invoke_once_and_transaction_rolls_back(base, runtime):
    name = "mod08_probe_" + uuid4().hex
    sequence = "mod08_probe_" + uuid4().hex
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SEQUENCE public.{}").format(sql.Identifier(sequence)))
        cursor.execute(sql.SQL("GRANT USAGE,SELECT ON SEQUENCE public.{} TO {}").format(
            sql.Identifier(sequence), sql.Identifier(runtime)))
        expected = install(cursor, name, sequence=sequence)
    try:
        set_role(runtime)
        with transaction.atomic(), recording() as captured, connection.cursor() as cursor:
            assert probe(cursor, name, expected)["trusted"]
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT last_value FROM public.{}").format(sql.Identifier(sequence)))
            assert cursor.fetchone()[0] == 1
        assert _replay_serial(captured["statements"]) == captured["digests"]
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT last_value FROM public.{}").format(sql.Identifier(sequence)))
            assert cursor.fetchone()[0] == 2
        with pytest.raises(RuntimeError, match="intentional"), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT set_config('mod08.probe_rollback','pending',true)")
            assert probe(cursor, name, expected)["trusted"]
            raise RuntimeError("intentional")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('mod08.probe_rollback',true)")
            assert cursor.fetchone()[0] != "pending"
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("DROP FUNCTION public.{}()").format(sql.Identifier(name)))
            cursor.execute(sql.SQL("DROP SEQUENCE public.{}").format(sql.Identifier(sequence)))


def test_alternating_diagnostic_timing_includes_attestation(helper, runtime, record_property):
    name, expected = helper
    set_role(runtime)
    metrics = {}
    for recorded in (False, True):
        samples = {"reference": [], "helper_attested": []}
        for iteration in range(22):
            order = ("reference", "helper_attested") if iteration % 2 == 0 else ("helper_attested", "reference")
            for variant in order:
                with transaction.atomic(), connection.cursor() as cursor:
                    start = perf_counter_ns()
                    if recorded:
                        with recording() as state:
                            value = reference(cursor) if variant == "reference" else probe(cursor, name, expected)
                        assert state["supported"]
                    else:
                        value = reference(cursor) if variant == "reference" else probe(cursor, name, expected)
                    elapsed = perf_counter_ns() - start
                assert value["trusted"]
                if iteration >= 2:
                    samples[variant].append(elapsed)
        metrics["recorded" if recorded else "plain"] = {
            variant: {"count": len(values), "median_ns": median(values), "samples_ns": values}
            for variant, values in samples.items()
        }
    record_property("runtime_sql_probe_diagnostic", json.dumps({
        "status": "DIAGNOSTIC_NOT_ACCEPTANCE", "metrics": metrics,
        "includes_attestation": True, "postgres_major": 17,
    }, sort_keys=True))
