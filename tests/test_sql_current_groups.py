"""Counterfactual attribution of current CASE groups; never a public bypass."""
import json
import os
import statistics
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from django.db import connection, transaction
from django.db.models import Q
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.core.models import VerificationCheck
from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv("SQL_CURRENT_GROUPS_OUTPUT"), reason="Explicit isolated current CASE diagnosis")]


@pytest.mark.parametrize("variant", ["contractual", "diverse"])
def test_current_groups(request, record_property, variant):
    request.getfixturevalue("directory")
    populate(10000)
    if variant == "diverse":
        revisions = list(Revision.objects.filter(status="approved").order_by("pk"))
        for index, revision in enumerate(revisions):
            suffix = alpha(index)
            revision.description += " " + suffix
            if revision.description_alternative:
                revision.description_alternative += " " + suffix
            revision.telegram = "bench" + suffix
        Revision.objects.bulk_update(revisions, ["description", "description_alternative", "telegram"], batch_size=250)
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    digest = projection.definitions_digest()
    assert projection.supported()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute("ANALYZE " + connection.ops.quote_name(table))
    modes = ["full", "omit_authority", "omit_content", "omit_checks", "omit_json", "omit_bulk_authority"]
    compiled, replacements = {}, {}
    original_member = proof.RowMembership.as_sql

    def without_check(self, compiler, conn, **kwargs):
        if self.source_expressions[-1].query.model is VerificationCheck:
            replacements["check"] = replacements.get("check", 0) + 1
            return "TRUE", []
        return original_member(self, compiler, conn, **kwargs)

    for family, data in [("listing", {}), ("search", {"q": "photography"})]:
        for mode in modes:
            captured = []
            with patch.object(proof, "read_publication_values", lambda read: captured.append(read) or []):
                with patch.object(proof, "authority_proof", return_value=Q()) if mode == "omit_authority" else patch.dict({}, {}):
                    with patch.object(proof, "content_proof", return_value=Q()) if mode == "omit_content" else patch.dict({}, {}):
                        with patch.object(proof, "bulk_authority_membership", return_value=Q()) if mode == "omit_bulk_authority" else patch.dict({}, {}):
                            with patch.object(proof.RowMembership, "as_sql", without_check) if mode == "omit_checks" else patch.dict({}, {}):
                                with patch.object(proof.JSONChoicesProof, "as_sql", return_value=("TRUE", [])) if mode == "omit_json" else patch.dict({}, {}):
                                    proof.SQLPublication(discovery.candidates(data))
            assert len(captured) == 1
            compiled[family, mode] = captured[0].sql, captured[0].params
    assert replacements == {"check": 2}
    assert projection.supported() and projection.definitions_digest() == digest
    output = Path(os.environ["SQL_CURRENT_GROUPS_OUTPUT"], variant + ".json")
    report = {"variant": variant, "source_fingerprint": digest, "stage": "compiled",
        "modes": modes, "query_patterns": {family+":"+mode: query_pattern(v[0]) for (family,mode),v in compiled.items()}}

    def persist():
        output.write_text(json.dumps(report, indent=2) + "\n")

    def read(family, mode, explain=False):
        sql, params = compiled[family, mode]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SET LOCAL statement_timeout='2000ms'")
            cursor.execute("SET LOCAL jit=off")
            if explain:
                cursor.execute("EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) " + sql, params)
                return redact_plan(cursor.fetchone()[0])
            start = time.perf_counter()
            cursor.execute(sql, params)
            executed = time.perf_counter() - start
            start = time.perf_counter()
            rows = cursor.fetchall()
            fetched = time.perf_counter() - start
            return rows, {"execute_seconds": executed, "fetch_seconds": fetched,
                "read_seconds": executed + fetched, "rows_returned": len(rows)}

    expected = {}
    for family in ["listing", "search"]:
        for mode in modes:
            rows, _ = read(family, mode)
            if mode == "full":
                assert len(rows) == 10000 and all(r[2] for r in rows)
                expected[family] = rows
            assert rows == expected[family]
    before = stats_snapshot()
    samples = []
    for cycle in range(8):
        order = modes[cycle % len(modes):] + modes[:cycle % len(modes)]
        if cycle % 2:
            order = list(reversed(order))
        for family in ["listing", "search"]:
            for mode in order:
                rows, values = read(family, mode)
                assert rows == expected[family]
                samples.append({"cycle": cycle, "family": family, "mode": mode, **values})
        report.update(stage="controls", samples=samples)
        persist()
    after = stats_snapshot()
    effects = {}
    for mode in modes[1:]:
        deltas = [statistics.mean(
            next(x["read_seconds"] for x in samples if x["cycle"] == cycle and x["family"] == family and x["mode"] == "full")
            - next(x["read_seconds"] for x in samples if x["cycle"] == cycle and x["family"] == family and x["mode"] == mode)
            for family in ["listing", "search"]) for cycle in range(8)]
        effects[mode] = {"paired_mean_family_deltas_seconds": deltas, "median_delta_seconds": statistics.median(deltas),
            "positive_cycles": sum(d > 0 for d in deltas),
            "diagnostic_priority": statistics.median(deltas) >= .05 and sum(d > 0 for d in deltas) >= 6}
    report.update(stage="plans", effects=effects, statistics_before=before, statistics_after=after,
        statistics_endpoints_equal=before == after,
        medians={family+":"+mode: statistics.median(x["read_seconds"] for x in samples if x["family"]==family and x["mode"]==mode)
            for family in ["listing", "search"] for mode in modes})
    persist()
    # Existing full CASE plans are reused; new counterfactuals get separate plans.
    plans = {mode: read("listing", mode, explain=True) for mode in modes[1:]}
    report.update(stage="complete", separate_counterfactual_plans=plans,
        scope="10000 original/diverse, current CASE/scalar/index. Isolated SQL counterfactuals ONLY, omitted rules never used in HTTP. Complete ordered vector matches all-valid fixture; not semantic equivalence or adoption. 8 balanced cyclic controls, same sources/data/stats. Deltas include joins/plan/order interactions and are nonadditive, not validation or CPU PG. Fetch output tuple length means rows_returned only; execute includes driver/PG/wait/buffering. No profiler. Plans run after controls and not combined with HTTP times. Group priority threshold is diagnostic only; any candidate still needs native equivalence and prefixed fullTCP effect both fixtures.",
        not_measured=["HTTP effect", "native equivalence of omitted rules (intentionally false)", "SQL rows_affected/scanned", "DB CPU/waits/locks/IO", "validation/render/materialization in this SQL-only diagnosis", "capacity"])
    assert projection.supported() and projection.definitions_digest() == digest
    persist()
    record_property("current_case_groups", json.dumps(report))
