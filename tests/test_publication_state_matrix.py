"""Current MOD05 route matrix; diagnostic timings are separate from controls."""

import hashlib
import io
import json
import os
import re
import statistics
import time
from collections import Counter, defaultdict

import pytest
from django.db import connection
from django.db.models.signals import post_init
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, publication_state, submissions
from apps.listings.forms import ContactsForm, DetailsForm
from apps.listings.models import Revision
from scripts.benchmark_rule_profile import RuleProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def prepare_population(count, fixture):
    populate(count)
    if fixture == "diverse":
        rows = list(Revision.objects.filter(status="approved").order_by("pk"))
        for i, row in enumerate(rows):
            row.description = f"Synthetic photography portrait session variation {i} with individual studio details."
            row.description_alternative = f"Synthetic companion studio description variant {i}."
            row.telegram = f"synthetic_matrix_{i}"
        Revision.objects.bulk_update(
            rows, ["description", "description_alternative", "telegram"], batch_size=250
        )
    if os.environ.get("PUBLICATION_MATRIX_DEPLOY") == "1":
        from django.core.management import call_command

        call_command("refresh_publication_state", stdout=io.StringIO())
    else:
        while publication_state.refresh(500):
            pass
    assert not publication_state.PublicationDirty.objects.exists()


@pytest.mark.parametrize("count", [100, 1000, 10000])
@pytest.mark.parametrize("fixture", ["repeated", "diverse"])
def test_current_stored_route_matrix(request, monkeypatch, record_property, count, fixture):
    client = request.getfixturevalue("directory")
    prepare_population(count, fixture)
    paths = ["/es/", "/en/?q=photography"]
    reports = []
    for path in paths:

        def fingerprint(response):
            return {
                "status": response.status_code,
                "count": response.context["page"].paginator.count,
                "ids": [str(r.pk) for r in response.context["page"].object_list],
                "body": hashlib.sha256(response.content).hexdigest(),
                "route": response.wsgi_request._publication_route,
            }

        warm = client.get(path)
        expected = fingerprint(warm)
        assert expected["status"] == 200 and expected["route"]["route"] == "state"
        if path == "/es/":
            assert expected["count"] == count
        controls = []
        for _ in range(5):
            start = time.perf_counter()
            response = client.get(path)
            controls.append(time.perf_counter() - start)
            assert fingerprint(response) == expected
        models = Counter()
        sql = defaultdict(lambda: {"calls": 0, "total_time": 0.0})
        profile = RuleProfile()

        def instantiated(sender, **kwargs):
            if sender._meta.app_label in {"listings", "core", "catalog", "safety", "mediafiles"}:
                models[sender._meta.label] += 1

        def sql_event(execute, query, params, many, context):
            normalized = re.sub(r"'(?:''|[^'])*'", "'[redacted]'", query)
            normalized = re.sub(r"\b\d+\b", "?", normalized)
            normalized = " ".join(normalized.split())
            start = time.perf_counter()
            try:
                return execute(query, params, many, context)
            finally:
                sql[normalized]["calls"] += 1
                sql[normalized]["total_time"] += time.perf_counter() - start

        with monkeypatch.context() as patch:
            for owner, name in [
                (publication_state, "validate_submission"),
                (moderation, "validate_submission"),
                (moderation, "publicly_visible"),
                (discovery, "render"),
                (submissions, "publication_ready"),
                (DetailsForm, "full_clean"),
                (ContactsForm, "full_clean"),
            ]:
                patch.setattr(
                    owner, name, profile.wrap(f"{owner.__name__}.{name}", getattr(owner, name))
                )
            post_init.connect(instantiated, weak=False)
            try:
                start = time.perf_counter()
                with connection.execute_wrapper(sql_event):
                    response = client.get(path)
                instrumented = time.perf_counter() - start
            finally:
                post_init.disconnect(instantiated)
        assert fingerprint(response) == expected
        dominant = [
            {"normalized": q, **v, "mean_time": v["total_time"] / v["calls"]}
            for q, v in sorted(sql.items(), key=lambda item: item[1]["total_time"], reverse=True)[
                :5
            ]
        ]
        reports.append(
            {
                "path": path,
                "count": expected["count"],
                "route": expected["route"],
                "controls_seconds": controls,
                "control_mean_seconds": statistics.mean(controls),
                "instrumented_seconds": instrumented,
                "queries": sum(v["calls"] for v in sql.values()),
                "driver_execute_seconds": sum(v["total_time"] for v in sql.values()),
                "dominant_driver_events": dominant,
                "materialized_instances": dict(models),
                "rule_events": profile.report(),
                "body_route_order_count_unchanged": True,
            }
        )
    record_property(
        "current_matrix", json.dumps({"count": count, "fixture": fixture, "routes": reports})
    )
    record_property(
        "limits",
        "PG/DjangoClient, not TCP/WSGI capacity. Warmup1 then controls5 then profiled1 per route; cache order bias, wrapper/post_init overhead not causally quantified. SQL driver events exclude fetch and are not PostgreSQL CPU/planning. Validation/render inclusive overlaps with SQL/lazy; RuleProfile exclusive subtracts only observed direct instrumented children. Instance counts are not SQL rows. rows_returned/affected/scanned, HTTP TCP, WSGI,D,CPU,construction/compilation and PG planning are not_measured. Diverse valid text/telegram changes only listed columns; shared synthetic photos/phones remain documented.",
    )
