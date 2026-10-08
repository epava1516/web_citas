"""Sequential TCP controls for current publication matrix, not capacity."""

import hashlib
import json
import os
import re
import signal
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from urllib.parse import quote, unquote

import pytest
from django.conf import settings
from django.core import signing
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_state_matrix import prepare_population

from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [100, 1000, 10000])
@pytest.mark.parametrize("fixture", ["repeated", "diverse"])
def test_current_matrix_tcp(request, tmp_path, record_property, count, fixture):
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
        f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        "PUBLICATION_STATE_READ_REPAIR = False\n"
        'MIDDLEWARE = MIDDLEWARE + ["scripts.publication_tcp_observer.RouteMiddleware"]\n'
    )
    env = os.environ.copy()
    env.update(
        POSTGRES_DB=connection.settings_dict["NAME"],
        DJANGO_SETTINGS_MODULE="tcp_runtime_settings",
        PYTHONPATH=str(tmp_path) + ":" + str(settings.BASE_DIR),
        PUBLICATION_TCP_EVENTS=str(tmp_path),
    )
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
                    "sync",
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
        for repeat in range(5):
            for index, path in enumerate(paths):
                rid = f"d-{repeat * 6 + index}"
                emission = time.monotonic()
                req = urllib.request.Request(origin + path, headers={"X-Benchmark-ID": rid})
                with urllib.request.urlopen(req, timeout=65) as r:
                    body = r.read()
                    status = r.status
                end = time.monotonic()
                assert status == 200 and canonical_hash(body, path) == expected[path], path
                samples.append(
                    {"id": rid, "path": path, "emission": emission, "end": end, "status": status}
                )
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
            if "/listing/" not in sample["path"]:
                assert event["route"]["route"] == "state" and event["route"]["native_unknown"] == 0
        report = []
        for path in paths:
            rows = [r for r in samples if r["path"] == path]
            report.append(
                {
                    "path": path,
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
                }
            ),
        )
        record_property(
            "limits",
            "Sequential HTTP TCP controls, five per route after warmup; own four sync workers; lightweight one event write/transaction plus route metadata middleware, no SQL/rule profiler, overhead not causally quantified. Same-host monotonic clocks; HTTP receipt can precede final WSGI close, no end>=exit assumption. No upload/concurrency/SLO capacity. CPU/resources not_measured; matrix populations not saturated historical populations. No backend before/after improvement claim.",
        )
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
