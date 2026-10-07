"""Contractual arrival-rate HTTP load on isolated local Gunicorn/PostgreSQL."""

import http.cookies
import json
import math
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.db import connection
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Revision
from scripts.benchmark_async_transport import POLICY, fetch_http, run_async_open_loop
from scripts.benchmark_gc_observer import GCObserver, generator_gc_overlap
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def percentile(values, ratio):
    return sorted(values)[max(0, math.ceil(len(values) * ratio) - 1)] if values else None


@pytest.mark.parametrize("scenario", ["functional", "short", "measured"])
def test_contract_arrival_rate_http_with_limited_uploads(request, tmp_path, record_property, scenario):
    large = scenario != "functional"
    upload_count = 15 if scenario == "measured" else 1
    request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    dataset = populate(10000 if large else 10)
    db = connection.settings_dict
    assert db["NAME"].startswith("test_promotion_gate_")
    environment = os.environ.copy()
    environment.update(
        POSTGRES_DB=db["NAME"],
        POSTGRES_USER=db["USER"],
        POSTGRES_PASSWORD=db["PASSWORD"],
        DB_HOST=db["HOST"],
        DB_PORT=str(db["PORT"]),
        APP_ENV="development",
        DJANGO_DEBUG="0",
        DJANGO_SETTINGS_MODULE="load_runtime_settings",
        PYTHONPATH=str(tmp_path) + os.pathsep + str(Path.cwd()),
        REDIS_URL="memory://",
        TASK_QUEUE_GENERATION="l" + uuid4().hex[:31],
    )
    (tmp_path / "load_runtime_settings.py").write_text(
        "from config.settings import *\n"
        + "MEDIA_ROOT = "
        + repr(str(django_settings.MEDIA_ROOT))
        + "\n"
        + "CELERY_TASK_ALWAYS_EAGER = True\nCELERY_TASK_EAGER_PROPAGATES = True\n"
        + 'CELERY_BEAT_SCHEDULE = {}\nCELERY_RESULT_BACKEND = "cache+memory://"\n'
    )
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    logfile = tmp_path / "gunicorn-private.log"
    accessfile = tmp_path / "gunicorn-access.log"
    rows, cold, uploads = [], [], []
    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version")
        postgres_version = cursor.fetchone()[0]
    resources = {
        "os": platform.platform(),
        "cpu_count": os.cpu_count(),
        "cpu_affinity_count": len(os.sched_getaffinity(0)),
        "postgres_version": postgres_version,
        "gunicorn_version": version("gunicorn"),
        "django_version": version("Django"),
        "python_version": platform.python_version(),
        "pg_server_shared": True,
        "limits": "Runner database isolated; PostgreSQL service/host shared with normal stack. No competing test/build workload; normal stack CPU load not instrumented.",
    }
    for name, file in [
        ("memory_total", "/proc/meminfo"),
        ("cgroup_memory_max", "/sys/fs/cgroup/memory.max"),
        ("cgroup_cpu_max", "/sys/fs/cgroup/cpu.max"),
    ]:
        if Path(file).is_file():
            value = Path(file).read_text()
            resources[name] = value.splitlines()[0] if name == "memory_total" else value.strip()
    process = None
    summary = {
        "dataset": dataset,
        "resources": resources,
        "success": False,
        "duration_seconds": {"functional": 3, "short": 60, "measured": 900}[scenario],
        "arrival_rps": 20,
        "server": "Gunicorn4 sync workers local TCP",
        "scope": "Synthetic local server capacity; external production/identity/CDN excluded. Upload processing eager in request, no real worker throughput claim.",
        "verdict": "INVALID",
        "invalid_reasons": ["workload_not_executed"],
        "policy": dict(POLICY),
        "mix": {
            "listing": "1/3",
            "search": "1/3",
            "detail": "1/3",
            "languages": "ES/EN alternating",
            "uploads": "separate1/minute,15 for contractual run",
        },
        "not_measured": [
            "app/DB CPU",
            "DB connections/waits/locks/IO",
            "worker/PostgreSQL RSS baseline/peak/final",
            "CPU/request",
            "allocations/request",
            "generator process CPU/RSS/scheduling outside observed GC intervals",
            "causal client GC callback overhead",
        ],
    }
    routes = [
        "/es/",
        "/en/",
        "/es/?q=photography",
        "/en/?q=synthetic",
        "/es/listing/" + dataset["sample_ids"][0] + "/",
        "/en/listing/" + dataset["sample_ids"][-1] + "/",
    ]

    async def concurrent_fetch(path, **kwargs):
        return await fetch_http(
            origin, path, timeout_seconds=POLICY["request_timeout_seconds"], **kwargs
        )

    artifact_folder = Path(request.config.getoption("--gate-timings-output")).parent
    manifest = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "dataset": dataset,
        "fixture": "seed_demo; deterministic photo seed1, upload seed782134; UUID identities/time-relative validity vary per isolated run",
        "resources": resources,
        "routes": routes,
        "mix": summary["mix"],
        "policy": dict(POLICY),
        "duration_seconds": summary["duration_seconds"],
        "arrival_rps": summary["arrival_rps"],
        "scheduled_dynamic": int(summary["duration_seconds"] * summary["arrival_rps"]),
        "uploads_separate": upload_count,
        "state": "Fresh Gunicorn/DB fixture; six cold probes then same-server sustained arrivals. OS/PG shared caches not reset or asserted cold",
        "error_policy": "Every non200 dynamic response, transport error or timeout is failed; uploads require302; final drain expiry classified failed/timeout",
        "instrumentation": "Monotonic per-request timestamps/async ledger; client-process GC callbacks during arrivals/drain with monotonic intervals and collector-thread CPU; event overlap reviewed after drain, causal callback overhead not_measured; GC policy unchanged; Gunicorn access logs; no app CPU/DB/RSS sampling",
        "scope": {"measured": "contractual", "short": "60s concurrent diagnostic only; not contractual capacity", "functional": "functional generator calibration only"}[scenario],
        "client": "asyncio local HTTP, no pending-request cap, total HTTP transaction deadline65s; no redirect following",
    }
    if scenario == "short":
        manifest["diagnostic_criteria"] = {
            "valid_generator_and_reconciled_accounting": True,
            "p95_seconds_strict_below": 0.8,
            "error_ratio_strict_below": 0.01,
            "uploads_expected_status": 302,
            "dynamic_pending_at_window_max": 20,
            "final_pending": 0,
            "reason": "Existing latency/error objectives plus at most one second of arrivals outstanding as accumulation filter; generator numeric policy unchanged. No capacity acceptance.",
        }
    (artifact_folder / "benchmark-manifest.json").write_text(json.dumps(manifest, indent=2))
    summary["frozen_manifest"] = manifest

    def fetch(path, *, data=None, headers=None, expected=200, scheduled=None, benchmark_id=None):
        begin = time.perf_counter()
        result = {
            "path": path,
            "expected": expected,
            "scheduled_lag_seconds": max(0, begin - scheduled) if scheduled else 0,
        }
        call_headers = dict(headers or {})
        if benchmark_id:
            call_headers["X-Benchmark-Id"] = benchmark_id
        request = urllib.request.Request(origin + path, data=data, headers=call_headers)
        try:
            try:
                response = urllib.request.build_opener(NoRedirect()).open(
                    request, timeout=POLICY["request_timeout_seconds"]
                )
            except urllib.error.HTTPError as error:
                response = error
            with response:
                payload = response.read()
                result.update(
                    status=response.code, bytes=len(payload), unexpected=response.code != expected
                )
        except (OSError, TimeoutError) as error:
            result.update(
                status=0,
                bytes=0,
                unexpected=True,
                error=type(error).__name__,
                timeout=isinstance(getattr(error, "reason", error), TimeoutError),
            )
        result["seconds"] = time.perf_counter() - begin
        return result

    try:
        with logfile.open("w") as output:
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
                    "--timeout",
                    "60",
                    "--access-logfile",
                    str(accessfile),
                    "--access-logformat",
                    "%(s)s %(L)s %(U)s %({x-benchmark-id}i)s",
                    "--error-logfile",
                    "-",
                    "--graceful-timeout",
                    "10",
                ],
                env=environment,
                stdout=output,
                stderr=output,
                start_new_session=True,
            )
        deadline = time.monotonic() + 30
        while True:
            assert process.poll() is None, "Gunicorn exited during startup"
            try:
                with urllib.request.urlopen(origin + "/health/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if time.monotonic() >= deadline:
                    raise AssertionError("Gunicorn did not become healthy")
                time.sleep(0.1)
        for path in routes:
            cold.append(fetch(path))
            if large and cold[-1]["unexpected"]:
                break
        summary["cold_probes"] = cold
        assert all(not row["unexpected"] for row in cold), (
            "Cold HTTP prerequisite failed; full workload not executed"
        )
        summary["cold_latency_seconds"] = {
            "p95": percentile([row["seconds"] for row in cold], 0.95),
            "population": len(cold),
        }
        manager = User.objects.get(username="fixture-v1-individual")
        person = Person.objects.get(individual=manager)
        client = Client()
        client.force_login(manager)
        cookies = http.cookies.SimpleCookie()
        with urllib.request.urlopen(origin + "/es/account/login/", timeout=65) as response:
            for value in response.headers.get_all("Set-Cookie", []):
                cookies.load(value)
        csrf = cookies[django_settings.CSRF_COOKIE_NAME].value
        cookie = f"{django_settings.SESSION_COOKIE_NAME}={client.cookies[django_settings.SESSION_COOKIE_NAME].value}; {django_settings.CSRF_COOKIE_NAME}={csrf}"
        draft_rows = Revision.objects.bulk_create(
            [
                Revision(listing=person.listing, manager_version=person.manager_version)
                for _ in range(16 if large else 1)
            ]
        )
        raw = raw_image(782134)
        boundary = "synthetic-" + uuid4().hex
        multipart = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="synthetic.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
            + raw
            + f"\r\n--{boundary}--\r\n".encode()
        )
        headers = {
            "Cookie": cookie,
            "X-CSRFToken": csrf,
            "Referer": origin + "/es/",
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        }
        upload_specs = [
            {
                "at": minute * 60,
                "path": f"/es/draft/{draft.pk}/photos/upload/",
                "data": multipart,
                "headers": headers,
                "expected": 302,
            }
            for minute, draft in enumerate(draft_rows[:upload_count])
        ]
        with GCObserver(monotonic_clock=time.monotonic) as client_gc:
            outcome = run_async_open_loop(
                concurrent_fetch,
                routes,
                duration=summary["duration_seconds"],
                rps=summary["arrival_rps"],
                upload_specs=upload_specs,
            )
        summary["client_gc"] = client_gc.report()
        assert summary["client_gc"]["policy_before"] == summary["client_gc"]["policy_after"]
        assert summary["client_gc"]["unfinished_events"] == 0
        summary["client_gc_emission_overlap"] = generator_gc_overlap(
            summary["client_gc"]["events"], outcome["samples"],
            outcome["monotonic_origin_seconds"],
        )
        summary.update(outcome)
        rows, uploads = outcome["samples"], outcome["uploads"]
        samples_path = (
            Path(request.config.getoption("--gate-timings-output")).parent
            / "benchmark-samples.json"
        )
        samples_path.write_text(
            json.dumps({"dynamic": rows, "uploads": uploads, "clock": outcome["clock"]}, indent=2)
        )
        summary["request_samples_artifact"] = str(samples_path)
        if scenario == "short":
            summary["diagnostic_checks"] = {
                "validity": summary["verdict"] != "INVALID",
                "latency_and_errors": summary["verdict"] == "PASS",
                "pending_at_window": summary["window_close"]["dynamic"]["pending"] <= 20,
                "final_pending": summary["counts"]["pending"] == 0,
                "upload": summary["final_upload_counts"]["successful"] == upload_count,
            }
            summary["diagnostic_continue_contract"] = all(summary["diagnostic_checks"].values())
        assert summary["counts"]["reconciled"] and summary["final_upload_counts"]["reconciled"]
        if not large:
            assert (
                summary["counts"]["failed"] == 0 and summary["final_upload_counts"]["failed"] == 0
            )
            assert summary["verdict"] != "INVALID", summary["invalid_reasons"]
        else:
            assert summary["verdict"] == "PASS", (
                summary["verdict"] + ": " + repr(summary["invalid_reasons"])
            )
        if scenario == "short":
            assert summary["diagnostic_continue_contract"], summary["diagnostic_checks"]
        summary["success"] = True
    finally:
        if process and process.poll() is None:
            import signal

            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        summary["gunicorn_stopped"] = process is None or process.poll() is not None
        if logfile.exists():
            import re

            summary["startup_error_types"] = re.findall(r"([A-Za-z]+Error):", logfile.read_text())[
                -10:
            ]
        summary["cold_probes"] = cold
        if accessfile.exists():
            server_rows = [line.split() for line in accessfile.read_text().splitlines()]
            dynamic_server = [
                row for row in server_rows if len(row) == 4 and row[3].startswith("d-")
            ]
            summary["gunicorn_dynamic_service_p95_seconds"] = percentile(
                [float(row[1]) for row in dynamic_server], 0.95
            )
            summary["gunicorn_dynamic_service_population"] = len(dynamic_server)
            summary["gunicorn_dynamic_service_limits"] = (
                "Completed Gunicorn log rows only; interrupted/unlogged/timeouts excluded here, included in observable latency/failed population. Health/cold/uploads excluded."
            )
        (tmp_path / "load-summary.json").write_text(json.dumps(summary, indent=2))
        compact = {key: value for key, value in summary.items() if key != "samples"}
        record_property("load_summary", json.dumps(compact))
