"""Bounded fresh-statistics/join-choice diagnosis of the previously aborted shape."""

import json
import os
import statistics
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from django.db import OperationalError, connection, transaction
from django.db.models import BooleanField, Case, Q, Value, When
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        not os.getenv("MEMBERSHIP_PLANNER_OUTPUT"),
        reason="Explicit bounded SQL-only planner diagnostic",
    ),
]


@pytest.mark.parametrize("variant", ["contractual", "diverse"])
def test_membership_estimates_statistics_and_bounded_join_choice(request, record_property, variant):
    request.getfixturevalue("directory")
    populate(10000)
    if variant == "diverse":
        rows = list(Revision.objects.filter(status="approved").order_by("pk"))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += " " + suffix
            if row.description_alternative:
                row.description_alternative += " " + suffix
            row.telegram = "bench" + suffix
        Revision.objects.bulk_update(
            rows, ["description", "description_alternative", "telegram"], batch_size=250
        )
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith(
        "test_promotion_gate_"
    )
    assert projection.supported()
    digest = projection.definitions_digest()
    document = proof.submissions.current_publishing_document()
    condition = proof.authority_proof(document, bulk=True) & proof.content_proof(bulk=True)
    compiled = {}
    for family, data in [("listing", {}), ("search", {"q": "photography"})]:
        query = discovery.candidates(data)
        ordering = proof.compact_order(query, 1)
        positive = query.filter(condition).order_by().values("pk")
        for mode, predicate in [("case", condition), ("membership", Q(pk__in=positive))]:
            selected = query.annotate(
                _sql_publication_positive=Case(
                    When(predicate, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            captured = []
            with patch.object(
                proof, "read_publication_values", lambda read: captured.append(read) or []
            ):
                proof.read_ordered_scalar_population(selected, ordering)
            assert len(captured) == 1
            compiled[family, mode] = captured[0].sql, captured[0].params
    output = Path(os.environ["MEMBERSHIP_PLANNER_OUTPUT"], variant + ".json")
    report = {
        "variant": variant,
        "stage": "prepared",
        "source_fingerprint": digest,
        "limits": "SQL-only, no HTTP or authority bypass in application; completecandidate vectors includingunknown flag, not population pruning. SETLOCAL only ownreadonlytransaction, no serverpolicy. CASE is currentbaseline. Membership identicalexpressioninWHERE as abortedprototype; stats/joinplan hypothesestested explicitly, oldabortnotreclassified.2sstatementtimeout/cancellation only onownedconnection. No repeat of a timeoutmode in timedcontrols. SQLrowreturned fromactualfetch only, planrows pernode not global rows_scanned. Execute+fetch wall includesdriver/PG/waits/buffering, not PGCPU. No model/validation/render/capacity/causalGUCoverheadmeasured. No adoption without nativeequivalence and completeHTTPeffect.",
    }

    def persist():
        output.write_text(json.dumps(report, indent=2) + "\n")

    def run(family, shape, nestloop=True, explain=None):
        sql, params = compiled[family, shape]
        started = time.perf_counter()
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SET LOCAL statement_timeout='2000ms'")
                cursor.execute("SET LOCAL jit=off")
                cursor.execute("SET LOCAL enable_nestloop=" + ("on" if nestloop else "off"))
                if explain:
                    cursor.execute(
                        (
                            "EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) "
                            if explain == "analyze"
                            else "EXPLAIN (SETTINGS, FORMAT JSON) "
                        )
                        + sql,
                        params,
                    )
                    return {
                        "status": "complete",
                        "plan": redact_plan(cursor.fetchone()[0]),
                        "query_pattern": query_pattern(sql),
                    }, None
                started = time.perf_counter()
                cursor.execute(sql, params)
                executed = time.perf_counter() - started
                started = time.perf_counter()
                rows = cursor.fetchall()
                fetched = time.perf_counter() - started
                return {
                    "status": "complete",
                    "execute_seconds": executed,
                    "fetch_seconds": fetched,
                    "read_seconds": executed + fetched,
                    "rows_returned": len(rows),
                }, rows
        except OperationalError as error:
            if getattr(error.__cause__, "sqlstate", None) != "57014":
                raise
            return {
                "status": "statement_timeout",
                "bounded_operation_wall_seconds": time.perf_counter() - started,
            }, None

    # Planned-only before ANALYZE. Never repeat the old unbounded preflight.
    report["stats_before_analyze"] = stats_snapshot()
    planned = []
    for family in ["listing", "search"]:
        for shape in ["case", "membership"]:
            value, _ = run(family, shape, explain="planned")
            planned.append({"family": family, "shape": shape, "nestloop": True, **value})
    report.update(stage="planned_before_analyze", plans_before_analyze=planned)
    persist()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute("ANALYZE " + connection.ops.quote_name(table))
    report["stats_after_analyze"] = stats_snapshot()
    modes = {
        "case": ("case", True),
        "membership": ("membership", True),
        "case_nestloop_off": ("case", False),
        "membership_nestloop_off": ("membership", False),
    }
    planned = []
    for family in ["listing", "search"]:
        for mode, (shape, nestloop) in modes.items():
            value, _ = run(family, shape, nestloop, explain="planned")
            planned.append({"family": family, "mode": mode, **value})
    report.update(stage="planned_after_analyze", plans_after_analyze=planned)
    persist()
    expected = {}
    preflight = []
    eligible = []
    for mode, (shape, nestloop) in modes.items():
        valid = True
        for family in ["listing", "search"]:
            value, rows = run(family, shape, nestloop)
            if value["status"] == "complete":
                if mode == "case":
                    assert len(rows) == 10000 and all(row[2] for row in rows)
                    expected[family] = rows
                assert rows == expected[family]
                value["complete_ordered_vectors_equal"] = True
            else:
                valid = False
            preflight.append({"family": family, "mode": mode, **value})
        if valid:
            eligible.append(mode)
    assert "case" in eligible
    report.update(stage="bounded_preflight", preflight=preflight, eligible_modes=eligible)
    persist()
    # Counterbalance each eligible alternative directly with the currentCASE.
    # If any timed statement times out, stop that mode without retrospective
    # replacement/retry; its paired effect is not_measured.
    samples = []
    failed_modes = []
    for alternative in [m for m in eligible if m != "case"]:
        failed = False
        for pair in range(8):
            for family in ["listing", "search"]:
                for mode in ["case", alternative] if pair % 2 == 0 else [alternative, "case"]:
                    value, rows = run(family, *modes[mode])
                    samples.append(
                        {
                            "alternative": alternative,
                            "pair": pair,
                            "family": family,
                            "mode": mode,
                            **value,
                        }
                    )
                    if value["status"] != "complete":
                        failed = True
                        break
                    assert rows == expected[family]
                if failed:
                    break
            if failed:
                break
        if failed:
            failed_modes.append(alternative)
        report.update(stage="controls", samples=samples, failed_timed_modes=failed_modes)
        persist()
    effects = {}
    for alt in [m for m in eligible if m != "case" and m not in failed_modes]:
        values = [s for s in samples if s["alternative"] == alt]
        medians = {
            f: {
                m: statistics.median(
                    s["read_seconds"] for s in values if s["family"] == f and s["mode"] == m
                )
                for m in ["case", alt]
            }
            for f in ["listing", "search"]
        }
        deltas = [
            statistics.mean(
                next(
                    s["read_seconds"]
                    for s in values
                    if s["pair"] == p and s["family"] == f and s["mode"] == "case"
                )
                - next(
                    s["read_seconds"]
                    for s in values
                    if s["pair"] == p and s["family"] == f and s["mode"] == alt
                )
                for f in ["listing", "search"]
            )
            for p in range(8)
        ]
        threshold = max(0.05, 0.20 * statistics.mean(v["case"] for v in medians.values()))
        effects[alt] = {
            "medians": medians,
            "deltas": deltas,
            "threshold_seconds": threshold,
            "material_sql_effect": statistics.median(deltas) >= threshold
            and sum(x > 0 for x in deltas) >= 6
            and all(v[alt] - v["case"] <= max(0.025, 0.10 * v["case"]) for v in medians.values()),
        }
    # Only completed, eligible shapes get ANALYZE plans, after all controls.
    analyzed = []
    for mode in eligible:
        if mode == "case" or mode in failed_modes:
            continue
        for family in ["listing", "search"]:
            plan, _ = run(family, *modes[mode], explain="analyze")
            analyzed.append({"family": family, "mode": mode, **plan})
    after = stats_snapshot()
    assert projection.supported() and projection.definitions_digest() == digest
    with connection.cursor() as cursor:
        cursor.execute("SHOW enable_nestloop")
        assert cursor.fetchone()[0] == "on"
        cursor.execute("SHOW statement_timeout")
        assert cursor.fetchone()[0] == "0"
    report.update(
        stage="complete",
        effects=effects,
        analyzed_plans=analyzed,
        stats_after=after,
        statistics_control_endpoints_equal=report["stats_after_analyze"] == after,
        localsettings_restored=True,
        backend_change=False,
        baseline_case_analyze_reused="docs/evidencias/listado-sql-captura-escalar-coste0110.json / separate_readonly_plans; same mainSQL, no extra baseline ANALYZE plan",
    )
    persist()
    record_property("membership_planner", json.dumps(report))
