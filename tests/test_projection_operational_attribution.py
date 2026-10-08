"""Opt-in coarse request observation and real-input key replay, without sys.setprofile."""
import hashlib
import json
import os
import statistics
import sys
import time
from collections import Counter
from contextlib import nullcontext
from functools import wraps
from pathlib import Path

import pytest
from django.db import connection
from django.utils.translation import get_language, override
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv("PROJECTION_OPERATIONAL_OUTPUT"), reason="Explicit isolated diagnostic only")]
ORDERS = [("plain", "coarse"), ("coarse", "plain"),
          ("plain", "coarse"), ("coarse", "plain")]


@pytest.mark.parametrize("variant", ["contractual", "diverse"])
def test_operational_stage_and_key_attribution(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue("directory")
    prepare_start = time.perf_counter()
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
            rows, ["description", "description_alternative", "telegram"], batch_size=250)
        del rows
    preparation_seconds = time.perf_counter() - prepare_start
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    assert sys.getprofile() is None and projection.supported()
    digest = projection.definitions_digest()

    # Native functional oracle, outside projected sample timings.
    with monkeypatch.context() as patch:
        patch.setattr(projection, "supported", lambda **kwargs: False)
        native = client.get("/es/")
    assert native.status_code == 200 and native.context["page"].paginator.count == 10000
    body = native.content
    expected_page = [row.pk for row in native.context["page"]]
    del native
    pattern_cache = {}
    population_hash = None

    def equivalent(response):
        assert response.status_code == 200 and response.content == body
        assert response.context["page"].paginator.count == 10000
        assert [row.pk for row in response.context["page"]] == expected_page
        route = response.wsgi_request._publication_route
        assert route["route"] == "projection"
        assert route["candidate_stats"]["positive"] == 10000
        assert route["candidate_stats"]["native_fallback"] == 0
        return route

    def measured_get(mode):
        nonlocal population_hash
        stages, patterns = {}, {}

        def observer(name, original):
            @wraps(original)
            def observed(*args, **kwargs):
                nonlocal population_hash
                start = time.perf_counter()
                try:
                    result = original(*args, **kwargs)
                finally:
                    stages[name] = time.perf_counter() - start
                if name == "eligibility_population":
                    actual = hashlib.sha256(b"".join(pk.bytes for pk in result)).hexdigest()
                    if population_hash is None:
                        population_hash = actual
                    assert population_hash == actual
                return result
            return observed

        def sql_timer(executor, sql, params, many, context):
            start = time.perf_counter()
            try:
                return executor(sql, params, many, context)
            finally:
                elapsed = time.perf_counter() - start
                if sql not in pattern_cache:
                    pattern_cache[sql] = query_pattern(sql)
                entry = patterns.setdefault(pattern_cache[sql], {"calls": 0, "total_time": 0.})
                entry["calls"] += 1
                entry["total_time"] += elapsed

        with monkeypatch.context() as patch:
            if mode == "coarse":
                for name, owner, attribute in [
                    ("projection_preparation", projection.ProjectedPublication, "__init__"),
                    ("eligibility_population", projection.ProjectedPublication, "visible_ids"),
                    ("render", discovery, "render"),
                ]:
                    patch.setattr(owner, attribute, observer(name, getattr(owner, attribute)))
            # Observation does not replace rule functions or bypass their fingerprint.
            assert projection.definitions_digest() == digest and projection.supported()
            start = time.perf_counter()
            with connection.execute_wrapper(sql_timer) if mode == "coarse" else nullcontext():
                response = client.get("/es/")
            elapsed = time.perf_counter() - start
            route = equivalent(response)
            assert projection.definitions_digest() == digest and sys.getprofile() is None
        return {"mode": mode, "request_seconds": elapsed, "stages": stages, "route": route,
                "queries": sum(p["calls"] for p in patterns.values()) if patterns else "not_measured",
                "sql_execute_seconds": sum(p["total_time"] for p in patterns.values()) if patterns else "not_measured",
                "dominant_sql": [{"query_pattern": p, **v, "mean_time": v["total_time"] / v["calls"]}
                                 for p, v in sorted(patterns.items(), key=lambda pair: pair[1]["total_time"], reverse=True)]}

    samples = []
    # Warm-up is explicit, not included among the four paired controls.
    equivalent(client.get("/es/"))
    before = stats_snapshot()
    for pair, order in enumerate(ORDERS):
        for mode in order:
            samples.append({"pair": pair, **measured_get(mode)})
    after = stats_snapshot()

    # Capture actual complete key inputs in a separate, untimed request. Keeping
    # inputs alive changes memory/GC; this request is never used as latency data.
    calls = []
    original = projection.ProjectedPublication.native_content

    @wraps(original)
    def capture(self, kind, data, instance, factory):
        calls.append((kind, get_language(), id(self.catalog), data))
        return original(self, kind, data, instance, factory)

    with monkeypatch.context() as patch:
        patch.setattr(projection.ProjectedPublication, "native_content", capture)
        assert projection.definitions_digest() == digest and projection.supported()
        capture_route = equivalent(client.get("/es/"))
        assert projection.definitions_digest() == digest
    assert len(calls) == 30000
    assert Counter(kind for kind, *_ in calls) == {"details": 10000, "contacts": 10000, "rates": 10000}
    replay_samples = []
    for _ in range(4):
        # Fresh memos reproduce successful hit/miss decisions in this fixture.
        # There are no validators, SQL or forms in this replay.
        memo = {kind: {} for kind in ("details", "contacts", "rates")}
        hits, misses = Counter(), Counter()
        start = time.perf_counter()
        with override("es"):
            for kind, language, catalog_id, data in calls:
                assert language == "es"
                key = (get_language(), catalog_id, projection.freeze(data))
                if key not in memo[kind]:
                    memo[kind][key] = True
                    misses[kind] += 1
                else:
                    hits[kind] += 1
        seconds = time.perf_counter() - start
        assert all(hits[kind] + misses[kind] == 10000 for kind in memo)
        assert all(misses[kind] == capture_route["candidate_stats"][kind + "_native"] for kind in memo)
        replay_samples.append({"seconds": seconds, "hits": dict(hits), "misses": dict(misses)})

    plain = [s["request_seconds"] for s in samples if s["mode"] == "plain"]
    coarse = [s["request_seconds"] for s in samples if s["mode"] == "coarse"]
    median_plain = statistics.median(plain)
    replay_median = statistics.median(s["seconds"] for s in replay_samples)
    pairs = [{s["mode"]: s["request_seconds"] for s in samples if s["pair"] == i}
             for i in range(4)]
    pair_deltas = [p["coarse"] - p["plain"] for p in pairs]
    report = {"schema": "projection-operational-attribution-v1", "variant": variant,
              "count": 10000, "preparation_seconds": preparation_seconds,
              "samples": samples, "statistics_before": before, "statistics_after": after,
              "ordered_population_sha256": population_hash,
              "rule_fingerprint_unchanged": projection.definitions_digest() == digest,
              "capture_calls": len(calls), "replay_samples": replay_samples,
              "median_plain_seconds": median_plain,
              "median_coarse_seconds": statistics.median(coarse),
              "median_paired_delta_seconds": statistics.median(pair_deltas),
              "coarse_observation_compatible": abs(statistics.median(pair_deltas)) <= max(.05, .1 * median_plain),
              "median_key_replay_seconds": replay_median,
              "key_candidate_warrants_pilot": replay_median >= .25 and replay_median >= .1 * median_plain,
              "scope": "Four AB/BA/AB/BA DjangoClient plain/coarse pairs. Coarse clocks only preparation, eligibility collection and render, plus SQL execute; rules/fingerprint unmodified and route/body/page invariant. No sys.setprofile/post_init. Stages contain nested SQL/lazy work and are not validation-only. Separate untimed capture holds real inputs; replay includes key creation/dict hit-miss/counters with fresh memos, excludes validation/SQL and is not a subtraction from HTTP or predicted saving. Ordered population digest compared among coarse samples; native HTTP checks total/page/body, not all native IDs. Shared warm caches/host, temporal variation and four pairs limit causal overhead inference; compatibility is a diagnostic criterion, not capacity.",
              "not_measured": ["causal profiler overhead", "unprofiled per-rule times", "SQL fetch/driver decoding separately",
                               "SQL rows_returned/affected/scanned", "model constructions", "DB_CPU_RSS_waits_IO",
                               "current concurrent capacity", "p95_request", "100/1000 matrix", "PRODUCTION/checked/promotion costs"]}
    record_property("operational_attribution", report)
    Path(os.environ["PROJECTION_OPERATIONAL_OUTPUT"], variant + ".json").write_text(
        json.dumps(report, indent=2) + "\n")
