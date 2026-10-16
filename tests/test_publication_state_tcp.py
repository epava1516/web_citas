"""Sequential TCP controls for current publication matrix, not capacity."""

import hashlib
import json
import os
import re
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote

import pytest
from django.conf import settings
from django.core import signing
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_state_matrix import prepare_population

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [100, 1000, 10000])
@pytest.mark.parametrize("fixture", ["repeated", "diverse"])
def test_current_matrix_tcp(request, tmp_path, record_property, count, fixture):
    from scripts.benchmark_server_topology import server_topology

    topology = server_topology(os.environ)
    threaded = topology["threads"] > 1
    if threaded:
        assert (count, fixture) == (100, "repeated"), "Bounded explicit threaded parity only"
    membership_contrast = os.environ.get("PUBLICATION_TCP_MEMBERSHIP_CONTRAST") == "1"
    order_contrast = membership_contrast or os.environ.get("PUBLICATION_TCP_ORDER_CONTRAST") == "1"
    if threaded:
        assert not order_contrast and os.environ.get("PUBLICATION_TCP_DIRTY_CONTRAST") != "1"
    repeats = 10 if membership_contrast else 5
    client = request.getfixturevalue("directory")
    prepare_population(count, fixture)
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    ids = list(Listing.objects.filter(status="published").values_list("pk", flat=True))
    paths = [
        "/es/",
        "/en/",
        "/es/?q=photography",
        "/en/?q=synthetic",
        f"/es/listing/{ids[0]}/",
        f"/en/listing/{ids[-1]}/",
    ]
    (tmp_path / "tcp_runtime_settings.py").write_text(
        "from config.settings import *\n"
        "assert DEBUG is False, 'TCP matrix requires the same DEBUG=0 as clean HTTP load'\n"
        f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        "PUBLICATION_STATE_READ_REPAIR = False\n"
        'MIDDLEWARE = MIDDLEWARE + ["scripts.publication_tcp_observer.RouteMiddleware"]\n'
    )
    if order_contrast:
        reference = settings.BASE_DIR / "docs/evidencias/mod05-orden-reference0110.py"
        with (tmp_path / "tcp_runtime_settings.py").open("a") as runtime:
            runtime.write(f"PUBLICATION_ORDER_REFERENCE = {str(reference)!r}\n")
            runtime.write(f"PUBLICATION_ORDER_REFERENCE_SHA256 = {hashlib.sha256(reference.read_bytes()).hexdigest()!r}\n")
            runtime.write('MIDDLEWARE = MIDDLEWARE + ["scripts.publication_order_benchmark.OrderVariantMiddleware"]\n')
    env = os.environ.copy()
    env.update(
        POSTGRES_DB=connection.settings_dict["NAME"],
        POSTGRES_USER=connection.settings_dict["USER"],
        POSTGRES_PASSWORD=connection.settings_dict["PASSWORD"],
        DB_HOST=connection.settings_dict["HOST"],
        DB_PORT=str(connection.settings_dict["PORT"]),
        APP_ENV="development",
        DJANGO_DEBUG="0",
        DJANGO_SETTINGS_MODULE="tcp_runtime_settings",
        PYTHONPATH=str(tmp_path) + ":" + str(settings.BASE_DIR),
        PUBLICATION_TCP_EVENTS=str(tmp_path),
    )
    record_property("runtime_debug", "False; explicitly aligned with clean HTTP load")
    samples = []
    process = None
    try:
        with (tmp_path / "gunicorn.log").open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "config.wsgi:application",
                    "--bind",
                    f"127.0.0.1:{port}",
                    "--workers",
                    "4",
                    "--worker-class",
                    topology["worker_class"],
                    "--threads",
                    str(topology["threads"]),
                    "--timeout",
                    "65",
                    "--config",
                    "python:scripts.publication_tcp_observer",
                ],
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        deadline = time.monotonic() + 30
        while True:
            assert process.poll() is None, "Own Gunicorn exited"
            try:
                with urllib.request.urlopen(origin + "/health/", timeout=1) as r:
                    if r.status == 200:
                        break
            except OSError:
                assert time.monotonic() < deadline, "Own server startup timeout"
                time.sleep(0.1)

        def canonical_hash(body, path):
            if "/listing/" not in path:
                return hashlib.sha256(body).hexdigest()
            listing = Listing.objects.get(pk=path.rstrip("/").split("/")[-1])
            matches = list(re.finditer(rb'([?&]target=)([^&"]+)', body))
            assert len(matches) == 1, "Exactly one signed public report target required"
            token = unquote(matches[0].group(2).decode())
            decoded = signing.loads(token, salt="public-report-target-v1", max_age=7200)
            expected_target = {
                "listing": str(listing.pk),
                "revision": str(listing.approved_revision_id),
            }
            assert decoded == expected_target, (
                "Signed target must bind exact current listing/revision"
            )
            replacement = quote(json.dumps(decoded, sort_keys=True)).encode()
            normalized = re.sub(rb'([?&]target=)([^&"]+)', lambda m: m.group(1) + replacement, body)
            return hashlib.sha256(normalized).hexdigest()

        expected = {}
        for path in paths:
            r = client.get(path, HTTP_HOST=f"127.0.0.1:{port}")
            assert r.status_code == 200
            expected[path] = canonical_hash(r.content, path)
            with urllib.request.urlopen(origin + path, timeout=65) as warm:
                assert warm.status == 200 and canonical_hash(warm.read(), path) == expected[path], (
                    path
                )
        if threaded:
            from concurrent.futures import ThreadPoolExecutor

            from django.db import connections

            def parallel_probe(item):
                index, path = item
                rid = f"d-{1000000 + index}"
                emission = time.monotonic()
                try:
                    req = urllib.request.Request(origin + path, headers={"X-Benchmark-ID": rid})
                    with urllib.request.urlopen(req, timeout=65) as response:
                        body, status = response.read(), response.status
                    end = time.monotonic()
                    assert status == 200 and canonical_hash(body, path) == expected[path]
                    return {"id": rid, "path": path, "emission": emission, "end": end,
                            "status": status, "phase": "parallel", "block": -1}
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=8) as pool:
                samples.extend(pool.map(parallel_probe, enumerate(paths * 4)))
        contrast = os.environ.get("PUBLICATION_TCP_DIRTY_CONTRAST") == "1"
        page_ids = [row.pk for row in client.get("/es/", HTTP_HOST=f"127.0.0.1:{port}").context["page"].object_list]
        target = Listing.objects.filter(status="published", person__agency__isnull=False).exclude(pk__in=page_ids).first() if contrast or order_contrast else None
        phases = ["before", "after", "after", "before"] if order_contrast else ["clean", "dirty", "dirty", "clean"] if contrast else ["clean"]
        if order_contrast:
            Revision.objects.bulk_create([Revision(listing=target, manager_version=target.person.manager_version)])
            assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == {target.pk}
            # Plans are collected separately; their timings are not HTTP controls.
            reference_namespace = vars(publication_state).copy()
            exec(compile(reference.read_bytes(), str(reference), "exec"), reference_namespace)
            candidate_function = publication_state._state_page
            from scripts.publication_order_benchmark import compatible_order_reference

            reference_function = compatible_order_reference(reference_namespace["_ordered_reference"])
            plans = []
            for variant, function in [("before", reference_function), ("after", candidate_function)]:
                captured = []
                def capture(execute, query, params, many, context):
                    if not query.lstrip().upper().startswith("SELECT") or " FROM " not in query.upper():
                        return execute(query, params, many, context)
                    with connection.cursor() as cursor:
                        cursor.execute("SHOW jit")
                        jit = cursor.fetchone()[0]
                    begin = time.perf_counter()
                    try:
                        return execute(query, params, many, context)
                    finally:
                        captured.append((time.perf_counter()-begin, query, params, jit))
                publication_state._state_page = function
                try:
                    with connection.execute_wrapper(capture):
                        response = client.get("/en/?q=synthetic", HTTP_HOST=f"127.0.0.1:{port}")
                    assert response.status_code == 200
                    assert canonical_hash(response.content, "/en/?q=synthetic") == expected["/en/?q=synthetic"]
                    assert response.wsgi_request._publication_route["native_unknown"] == 1
                finally:
                    publication_state._state_page = candidate_function
                if membership_contrast:
                    # Match the affected operations, not whichever three reads
                    # happen to become dominant after the intervention.
                    selected_reads = [
                        row for row in captured
                        if '"listings_publicationstate"' in row[1]
                        and row[1].startswith((
                            'SELECT DISTINCT "listings_listing"."id" AS "pk"',
                            'SELECT "listings_listing"."id" AS "pk"',
                            'SELECT COUNT(*) AS "__count" FROM "listings_listing"',
                        ))
                    ]
                    assert len(selected_reads) == 3, "Unknown/count/final-page reads required"
                else:
                    selected_reads = sorted(captured, reverse=True, key=lambda item:item[0])[:3]
                for driver_time, query, params, jit in selected_reads:
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute("SET TRANSACTION READ ONLY")
                            cursor.execute("SET LOCAL statement_timeout='65s'")
                            cursor.execute("SET LOCAL jit=" + ("on" if jit == "on" else "off"))
                            cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query, params)
                            plan = cursor.fetchone()[0]
                    def redact(value):
                        if isinstance(value, dict):
                            return {k:redact(v) for k,v in value.items()}
                        if isinstance(value, list):
                            return [redact(v) for v in value]
                        if isinstance(value, str):
                            return re.sub(r"'(?:''|[^'])*'", "'[redacted]'", value)
                        return value
                    normalized = re.sub(r"'(?:''|[^'])*'", "'[redacted]'", query)
                    plans.append({"variant":variant,"normalized":normalized,"driver_execute_seconds":driver_time,"jit":jit,"plan":redact(plan)})
            record_property("order_plans", json.dumps(plans))

        if order_contrast:
            for phase in ["before", "after"]:
                for path in paths:
                    req = urllib.request.Request(origin + path, headers={"X-Order-Variant":phase})
                    with urllib.request.urlopen(req, timeout=65) as warm:
                        assert warm.status == 200 and canonical_hash(warm.read(), path) == expected[path]
        for block, phase in enumerate(phases):
            if contrast:
                if phase == "dirty":
                    Revision.objects.bulk_create([Revision(listing=target, manager_version=target.person.manager_version)])
                    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == {target.pk}
                else:
                    while publication_state.refresh(500):
                        pass
                    assert not PublicationDirty.objects.exists()
            for repeat in range(repeats):
                for index, path in enumerate(paths):
                    rid = f"d-{block * repeats * 6 + repeat * 6 + index}"
                    emission = time.monotonic()
                    req = urllib.request.Request(origin + path, headers={"X-Benchmark-ID": rid, "X-Order-Variant": phase if order_contrast else "after"})
                    with urllib.request.urlopen(req, timeout=65) as r:
                        body = r.read()
                        status = r.status
                    end = time.monotonic()
                    assert status == 200 and canonical_hash(body, path) == expected[path], path
                    samples.append({"id": rid, "path": path, "emission": emission, "end": end,
                                    "status": status, "phase": phase, "block": block})
        events = []
        deadline = time.monotonic() + 5
        while True:
            events = [
                json.loads(line)
                for f in tmp_path.glob("worker-*.jsonl")
                for line in f.read_text().splitlines()
            ]
            if len(events) == len(samples):
                break
            assert time.monotonic() < deadline, "WSGI records incomplete"
            time.sleep(0.1)
        byid = {e["id"]: e for e in events}
        assert len(byid) == len(samples)
        for sample in samples:
            event = byid[sample["id"]]
            assert sample["emission"] <= event["entry"] <= event["exit"]
            if order_contrast:
                assert event["order_variant"] == sample["phase"]
            if "/listing/" not in sample["path"]:
                assert event["route"]["route"] == "state" and event["route"]["native_unknown"] == (1 if order_contrast or sample["phase"] == "dirty" else 0)
        if threaded:
            parallel_events = [byid[row["id"]] for row in samples if row["phase"] == "parallel"]
            assert any(a["pid"] == b["pid"] and a["entry"] < b["exit"] and b["entry"] < a["exit"]
                       for i, a in enumerate(parallel_events) for b in parallel_events[i + 1:]), (
                "Prove actual overlapping WSGI requests in one worker process"
            )
        report = []
        for phase, path in [(phase, path) for phase in sorted({r["phase"] for r in samples}) for path in paths]:
            rows = [r for r in samples if r["path"] == path and r["phase"] == phase]
            report.append(
                {
                    "path": path,
                    "phase": phase,
                    "population": len(rows),
                    "http_mean_seconds": statistics.mean(r["end"] - r["emission"] for r in rows),
                    "wsgi_mean_seconds": statistics.mean(
                        byid[r["id"]]["exit"] - byid[r["id"]]["entry"] for r in rows
                    ),
                    "pre_wsgi_mean_seconds": statistics.mean(
                        byid[r["id"]]["entry"] - r["emission"] for r in rows
                    ),
                }
            )
        record_property(
            "tcp_matrix",
            json.dumps(
                {
                    "count": count,
                    "fixture": fixture,
                    "routes": report,
                    "samples": samples,
                    "wsgi_events": events,
                    "workers": 4,
                    "server_topology": topology,
                    "concurrent_client_limit": 8 if threaded else 1,
                    "dirty_contrast": contrast,
                    "order_contrast": order_contrast,
                    "membership_contrast": membership_contrast,
                    "controls_per_route_per_block": repeats,
                    "blocks": phases,
                }
            ),
        )
        record_property(
            "limits",
            ("Own gthread4x2,24 concurrent body parity controls with8 clients and proven same-PID WSGI overlap; "
             if threaded else "") + f"Sequential HTTP TCP controls, {repeats} per route/block after warmup; own four {topology['worker_class']} workers; lightweight one event write/transaction plus route metadata middleware, no SQL/rule profiler, overhead not causally quantified. Same-host monotonic clocks; HTTP receipt can precede final WSGI close, no end>=exit assumption. No upload/concurrency/SLO capacity. CPU/resources not_measured; matrix populations not saturated historical populations. Effect acceptance requires independent prefixed review.",
        )
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        # Preserve the original records for matrix controls too, after the own
        # server is stopped and before pytest removes its temporary directory.
        artifact_prefix = "order-tcp" if order_contrast else "matrix-tcp"
        artifact_folder = Path(request.config.getoption("--gate-timings-output")).parent / f"{artifact_prefix}-{fixture}-{count}"
        artifact_folder.mkdir(exist_ok=True)
        for log_file in [tmp_path / "gunicorn.log", *tmp_path.glob("worker-*.jsonl")]:
            if log_file.exists():
                shutil.copy2(log_file, artifact_folder / log_file.name)
