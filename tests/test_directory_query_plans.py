"""Finite real-PG query-plan diagnosis, own synthetic sources only."""

import hashlib
import json
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def stripped(node):
    allowed = {
        "Node Type",
        "Relation Name",
        "Index Name",
        "Join Type",
        "Strategy",
        "Actual Rows",
        "Actual Loops",
        "Actual Total Time",
        "Actual Startup Time",
        "Plan Rows",
        "Total Cost",
        "Shared Hit Blocks",
        "Shared Read Blocks",
        "Temp Read Blocks",
        "Temp Written Blocks",
        "Rows Removed by Filter",
        "Rows Removed by Join Filter",
        "Sort Method",
        "Sort Space Used",
    }
    row = {key: value for key, value in node.items() if key in allowed}
    if "Plans" in node:
        row["Plans"] = [stripped(child) for child in node["Plans"]]
    return row


def test_owned_directory_count_and_page_plans(request, record_property):
    if not any(
        str(arg).split("::")[0] == "tests/test_directory_query_plans.py"
        for arg in request.config.args
    ):
        pytest.skip("Explicit owned SQL-plan diagnostic only")
    client = request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    populate(10000)
    call_command("refresh_publication_state")
    cases = []
    for params in [{}, {"q": "photography"}, {"q": "synthetic"}]:
        captured = []

        def capture(execute, sql, values, many, context):
            if not sql.lstrip().upper().startswith("SELECT"):
                return execute(sql, values, many, context)
            if '"_pv_history"' in sql:
                captured.append(("hydration", sql, values))
            elif '"listings_publicationstate"' in sql and '"eligible"' in sql:
                captured.append(("population", sql, values))
            return execute(sql, values, many, context)

        with connection.execute_wrapper(capture):
            response = client.get("/es/", params)
        assert response.status_code == 200
        assert response.wsgi_request._publication_route["route"] == "state"
        assert 1 <= sum(kind == "population" for kind, _, _ in captured) <= 2
        assert sum(kind == "hydration" for kind, _, _ in captured) == 1
        rows = []
        for kind, sql, values in captured:
            # Match the actual page-hydration policy; transaction exit restores
            # these diagnostic-only GUCs without changing session defaults.
            with transaction.atomic(), connection.cursor() as cursor:
                if kind == "hydration":
                    cursor.execute("SET LOCAL jit=off")
                    cursor.execute("SET LOCAL join_collapse_limit=1")
                cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, values)
                plan = cursor.fetchone()[0][0]
            rows.append(
                {
                    "kind": "hydration" if kind == "hydration" else (
                        "count_and_page" if "OVER ()" in sql else ("count" if "COUNT(" in sql else "page")
                    ),
                    "local_policy": {"jit": "off", "join_collapse_limit": "1"}
                    if kind == "hydration" else {},
                    "fingerprint": hashlib.sha256(sql.encode()).hexdigest(),
                    "planning_ms": plan["Planning Time"],
                    "execution_ms": plan["Execution Time"],
                    "plan": stripped(plan["Plan"]),
                }
            )
        cases.append(
            {
                "search": params.get("q", ""),
                "count": response.context["page"].paginator.count,
                "queries": rows,
            }
        )
    target = (
        Path(request.config.getoption("--gate-timings-output")).parent
        / "directory-query-plans.json"
    )
    target.write_text(json.dumps(cases, indent=2) + "\n")
    record_property("plan_artifact", str(target))
    record_property(
        "scope", "Owned synthetic 10k fixture, sequential query EXPLAIN only; not HTTP p95/capacity"
    )
