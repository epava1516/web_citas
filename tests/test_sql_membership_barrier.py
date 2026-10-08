"""Keep cross-record checks out of join keys without changing their truth domain."""

import json
import os
import statistics
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from django.db import OperationalError, connection, transaction
from django.db.models import BooleanField, Case, F, Q, Value, When
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.core.models import Person
from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Listing, Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        not os.getenv("MEMBERSHIP_BARRIER_OUTPUT"),
        reason="Explicit bounded SQL join-key diagnostic only",
    ),
]


def truth(condition):
    return Q(
        Case(When(condition, then=Value(True)), default=Value(False), output_field=BooleanField())
    )


def crossfield_barrier(authority):
    changed = []

    def visit(node, monotone=True):
        if isinstance(node, Q):
            result = Q()
            result.connector = node.connector
            result.negated = node.negated
            result.children = [
                visit(c, monotone and not node.negated and node.connector == "AND")
                for c in node.children
            ]
            return result
        if (
            isinstance(node, tuple)
            and node[0].startswith("approved_revision__")
            and isinstance(node[1], F)
        ):
            assert monotone
            changed.append(node[0])
            return truth(Q(**{node[0]: node[1]}))
        return node

    result = visit(authority)
    assert set(changed) == {
        "approved_revision__listing_id",
        "approved_revision__manager_version",
        "approved_revision__phone",
    }
    return result


@pytest.mark.parametrize("variant", ["contractual", "diverse"])
def test_bounded_semantic_barrier_sql_cost(request, record_property, variant):
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
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute("ANALYZE " + connection.ops.quote_name(table))
    document = proof.submissions.current_publishing_document()
    authority = proof.authority_proof(document, bulk=True)
    content = proof.content_proof(bulk=True)
    conditions = {
        "case": authority & content,
        "authority_case": truth(authority) & content,
        "crossfield_case": crossfield_barrier(authority) & content,
    }
    compiled = {}
    for family, data in [("listing", {}), ("search", {"q": "photography"})]:
        query = discovery.candidates(data)
        ordering = proof.compact_order(query, 1)
        for mode, condition in conditions.items():
            predicate = (
                condition
                if mode == "case"
                else Q(pk__in=query.filter(condition).order_by().values("pk"))
            )
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
    output = Path(os.environ["MEMBERSHIP_BARRIER_OUTPUT"], variant + ".json")
    report = {
        "variant": variant,
        "stage": "prepared",
        "source_fingerprint": digest,
        "scope": "SQL-only no publicpath/backendchange. Original completecandidate CASE versus membership positives with authorityCASE or three cross-table equalityCASE barriers. TRUE domain unchanged for monotone positive comparisons; no rule removed. No newplannerGUC, jitoff only existingreadpolicy; everySQL<=2s. Planned estimates not actual join multiplicities; no PostgreSQLCPU attribution. Fullvectorcomparison and few offpage mutations, not full nativefunctionalacceptance. Exactfetch rows_returned, not affected/scanned; params neverexported.",
    }

    def persist():
        output.write_text(json.dumps(report, indent=2) + "\n")

    def run(family, mode, *, explain=None, readonly=True):
        sql, params = compiled[family, mode]
        start = time.perf_counter()
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                if readonly:
                    cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SET LOCAL statement_timeout='2000ms'")
                cursor.execute("SET LOCAL jit=off")
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
                start = time.perf_counter()
                cursor.execute(sql, params)
                executed = time.perf_counter() - start
                start = time.perf_counter()
                rows = cursor.fetchall()
                fetched = time.perf_counter() - start
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
                "bounded_operation_wall_seconds": time.perf_counter() - start,
            }, None

    plans = []
    for family in ["listing", "search"]:
        for mode in ["authority_case", "crossfield_case"]:
            p, _ = run(family, mode, explain="planned")
            plans.append({"family": family, "mode": mode, **p})
    report.update(planned=plans, stage="planned")
    persist()
    expected = {}
    preflight = []
    eligible = []
    for mode in conditions:
        valid = True
        for family in ["listing", "search"]:
            value, rows = run(family, mode)
            if rows is None:
                valid = False
            else:
                if mode == "case":
                    assert len(rows) == 10000 and all(r[2] for r in rows)
                    expected[family] = rows
                assert rows == expected[family]
                value["complete_ordered_vectors_equal"] = True
            preflight.append({"family": family, "mode": mode, **value})
        if valid:
            eligible.append(mode)
    assert "case" in eligible
    report.update(stage="preflight", preflight=preflight, eligible_modes=eligible)
    persist()
    mutations = []
    if len(eligible) > 1:
        target = Listing.objects.get(pk=expected["listing"][25][0])
        assert str(target.pk) not in [r[0] for r in expected["listing"][:24]]
        for model, pk, values in [
            (Revision, target.approved_revision_id, {"description": "www.example.invalid"}),
            (Revision, target.approved_revision_id, {"description": "Texto válido 😀"}),
            (Revision, target.approved_revision_id, {"manager_version": 998}),
            (Revision, target.approved_revision_id, {"phone": "+34600000998"}),
            (Person, target.person_id, {"consent_revoked_at": timezone.now()}),
        ]:
            with transaction.atomic():
                model.objects.filter(pk=pk).update(**values)
                for family in ["listing", "search"]:
                    baseline, rows = run(family, "case", readonly=False)
                    assert rows is not None
                    if family == "listing":
                        assert len(rows) == 10000 and sum(r[2] for r in rows) == 9999
                    for mode in eligible:
                        if mode == "case":
                            continue
                        val, other = run(family, mode, readonly=False)
                        assert other == rows, (mode, val["status"])
                transaction.set_rollback(True)
            mutations.append(sorted(values))
    report.update(stage="offpage_equivalence", mutation_fields=mutations)
    persist()
    before = stats_snapshot()
    samples = []
    failed = []
    for alt in [m for m in eligible if m != "case"]:
        stop = False
        for pair in range(8):
            for family in ["listing", "search"]:
                for mode in ["case", alt] if pair % 2 == 0 else [alt, "case"]:
                    value, rows = run(family, mode)
                    samples.append(
                        {"alternative": alt, "pair": pair, "family": family, "mode": mode, **value}
                    )
                    if rows is None:
                        stop = True
                        break
                    assert rows == expected[family]
                if stop:
                    break
            if stop:
                break
        if stop:
            failed.append(alt)
        report.update(stage="controls", samples=samples, failed_modes=failed)
        persist()
    effects = {}
    for alt in [m for m in eligible if m != "case" and m not in failed]:
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
    after = stats_snapshot()
    analyzed = []
    for mode in [m for m in eligible if m != "case" and m not in failed]:
        for family in ["listing", "search"]:
            plan, _ = run(family, mode, explain="analyze")
            analyzed.append({"family": family, "mode": mode, **plan})
    assert projection.supported() and projection.definitions_digest() == digest
    report.update(
        stage="complete",
        effects=effects,
        analyzed=analyzed,
        stats_before=before,
        stats_after=after,
        statistics_endpoints_equal=before == after,
        backend_changed=False,
        baseline_plans_reused="CurrentCASE analyzed plans from scalar effect, no duplicate.",
        not_measured=[
            "HTTPeffect/nativefullfunctionalacceptance",
            "PGCPU/RSS/waits/locks/IO",
            "globalrows_affected/scanned",
            "capacity",
        ],
    )
    persist()
    record_property("membership_barrier", json.dumps(report))
