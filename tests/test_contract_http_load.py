"""Contractual arrival-rate HTTP load on isolated local Gunicorn/PostgreSQL."""

import http.cookies
import io
import json
import math
import os
import platform
import signal as signal_module
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
from django.core.management import call_command
from django.db import connection
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import PublicationDirty, Revision
from scripts.benchmark_async_transport import POLICY, fetch_http, run_async_open_loop
from scripts.benchmark_gc_observer import GCObserver, generator_gc_overlap, prepare_generator_gc
from scripts.benchmark_publication_sampler import PublicationSampler
from scripts.benchmark_worker_observer import collect_events
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

# Refresh scenarios (docs/criterios-revision-benchmark-carga.md): default keeps the eager
# configuration of every previous run; normal_worker_beat runs owned worker/Beat as deployed.
EAGER = "without_worker_beat_eager_signal"
NORMAL = "normal_worker_beat"


def cpu_ticks(pids):
    total = {}
    for pid in pids:
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            total[pid] = int(fields[11]) + int(fields[12])
        except OSError:
            total[pid] = None
    return total


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def percentile(values, ratio):
    return sorted(values)[max(0, math.ceil(len(values) * ratio) - 1)] if values else None


@pytest.mark.parametrize("scenario", ["functional", "short", "measured"])
def test_contract_arrival_rate_http_with_limited_uploads(request, tmp_path, record_property, scenario):
    from scripts.benchmark_server_topology import server_topology

    topology = server_topology(os.environ)
    if topology["threads"] > 1:
        assert scenario in {"functional", "short"}, "Threaded candidate is not a contractual measurement"
    observe_workers = os.environ.get("WEB_MODELOS_BENCHMARK_OBSERVE_WORKERS") == "1"
    ingress_only = os.environ.get("WEB_MODELOS_BENCHMARK_INGRESS_ONLY") == "1"
    resource_only = os.environ.get("WEB_MODELOS_BENCHMARK_RESOURCE_ONLY") == "1"
    assert not ingress_only or (observe_workers and not resource_only and topology["threads"] == 1)
    assert not resource_only or observe_workers, "Resource-only mode requires explicit diagnostic observer"
    refresh_mode = os.environ.get("WEB_MODELOS_REFRESH_MODE", EAGER)
    assert refresh_mode in (EAGER, NORMAL)
    assert not (observe_workers and scenario == "measured"), "Worker observer is diagnostic only"
    large = scenario != "functional"
    upload_count = 15 if scenario == "measured" else 1
    request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    dataset = populate(10000 if large else 10)
    # MOD-05 deployment step (README/docs85): recompute stored publication state with the
    # code under test before serving traffic; bulk fixtures leave every listing marked.
    deploy_output = io.StringIO()
    call_command("refresh_publication_state", stdout=deploy_output)
    dataset["deployment_step"] = deploy_output.getvalue().strip()
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
    runtime_settings = (
        "from config.settings import *\n"
        + "MEDIA_ROOT = "
        + repr(str(django_settings.MEDIA_ROOT))
        + "\n"
    )
    if refresh_mode == EAGER:
        runtime_settings += (
            "CELERY_TASK_ALWAYS_EAGER = True\nCELERY_TASK_EAGER_PROPAGATES = True\n"
            + 'CELERY_BEAT_SCHEDULE = {}\nCELERY_RESULT_BACKEND = "cache+memory://"\n'
        )
    else:
        from test_worker_capacity_comparison import OBSERVER_SETTINGS, OWNED_REDIS

        # Deployed Celery configuration and Beat schedule; owned empty broker database.
        runtime_settings += OBSERVER_SETTINGS
        environment["REDIS_URL"] = OWNED_REDIS
    (tmp_path / "load_runtime_settings.py").write_text(runtime_settings)
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
    from apps.safety.canonical_kernel_loader import kernel_identity

    resources = {
        "canonical_kernel": kernel_identity(),
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
    celery_processes, sampler = {}, None
    summary = {
        "refresh_mode": refresh_mode,
        "dataset": dataset,
        "resources": resources,
        "success": False,
        "duration_seconds": {"functional": 3, "short": 60, "measured": 900}[scenario],
        "arrival_rps": 20,
        "server": f"Gunicorn4 {topology['worker_class']} workers, {topology['threads']} threads each, local TCP",
        "server_topology": topology,
        "scope": "Synthetic local server capacity; external production/identity/CDN excluded. "
        + ("Upload processing eager in request, no real worker throughput claim." if refresh_mode == EAGER
           else "Owned Celery worker (concurrency 2) and Beat as deployed; upload processing and MOD05 refresh in the worker."),
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
    observer_folder = artifact_folder / "worker-events-raw"
    observer_args = []
    if observe_workers:
        observer_folder.mkdir(mode=0o700)
        environment["WEB_MODELOS_BENCHMARK_OBSERVER_DIR"] = str(observer_folder)
        module = ("scripts.benchmark_gthread_observer" if topology["worker_class"] == "gthread"
                  else "scripts.benchmark_resource_observer") if resource_only else "scripts.benchmark_worker_observer"
        if ingress_only:
            module = "scripts.benchmark_ingress_observer"
        observer_args = ["--config", "python:" + module]
    manifest = {
        "refresh_mode": refresh_mode,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "server_topology": topology,
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
        "client_fixture_preparation": "One gc.collect(2) after fixture/auth/upload construction, before arrival clock; enabled/thresholds unchanged, automatic GC remains active during load. Previous observed client GC321.913ms overlaps273.107ms of273.462ms maximum emission delay; no backend improvement attributed to this preparation",
    }
    manifest["worker_observer"] = {
        "enabled": observe_workers,
        "mode": "route_only" if os.environ.get("WEB_MODELOS_BENCHMARK_ROUTE_ONLY") == "1" else "legacy_wrapped_phases",
        "scope": "Synthetic IDs already emitted by client; WSGI entry/end, inclusive context/validation/render and SQL execute wall/thread CPU; validation snapshots each1000calls, partial events retained; no real URI/SQL/parameters; not TCP accept or exact queue time; causal overhead not_measured",
        "clock": "time.monotonic in local worker processes; client loop.time origin explicitly recorded; same-host clock comparability checked after terminal",
        "phase_overlap": "SQL may be inside context/validation/render; native lazy evaluation/GC included in caller intervals; no additive phase partition",
    }
    if observe_workers and os.environ.get("WEB_MODELOS_BENCHMARK_ROUTE_ONLY") == "1":
        manifest["worker_observer"]["scope"] = "Route events after Django get_response; native handlers distinguished from discovery projection/fallback; WSGI start/end/render/SQL wall and threadCPU. No wrappers on native rules; context/validation not_measured. Requests without Django response/route event remain not_measured, never inferred from HTTP status. Partial work lower bounds; causal overhead not_measured."
    if ingress_only:
        manifest["worker_observer"].update(
            mode="ingress_sql_gc_no_handler_imports",
            scope="WSGI entry/end/threadCPU, SQL execute wall/threadCPU and GC only. "
                  "No eager imports or wrappers of handlers/rules/render; context/validation/render "
                  "not measured separately. SQL and GC overlap WSGI and each other. "
                  "Emission→WSGI includes client/TCP/scheduling/admission, not exact socket queue. "
                  "Observer overhead not measured causally; not a clean p95.",
        )
    if observe_workers:
        manifest["instrumentation"] += "; opt-in isolated worker observer as described in worker_observer, thread CPU scoped to WSGI request; opt-in workerGC intervals without policy changes, overlapping stages not additive; no per-request DB CPU/RSS sampling"
    if resource_only:
        manifest["worker_observer"].update(
            mode="resource_gthread_admission" if topology["worker_class"] == "gthread" else "resource_light",
            scope="WSGI start/end/threadCPU and route; gthread includes connection-created/enqueue-call/handler-entry timestamps. No SQL/render/rule wrappers. SQL/stages not_measured, not zero. Same-host monotonic; enqueue interval includes setup/submission, not exact exclusive queue; causal overhead not_measured.",
        )
        manifest["instrumentation"] = (
            "Existing asyncledger/clientGC and lightweight WSGI/route/threadCPU only; "
            "no SQL/render/rule wrappers or profiler; ownCPU cgroup collector separately documented."
        )
    if scenario == "short":
        assert manifest["policy"]["request_timeout_seconds"] == 65
        assert manifest["policy"]["drain_seconds"] == 70
        assert manifest["duration_seconds"] == 60 and manifest["arrival_rps"] == 20
        assert manifest["dataset"]["published"] == 10000
        manifest["diagnostic_criteria"] = {
            "valid_generator_and_reconciled_accounting": True,
            "p95_seconds_strict_below": 0.8,
            "error_ratio_strict_below": 0.01,
            "uploads_expected_status": 302,
            "dynamic_pending_at_window_max": 20,
            "final_pending": 0,
            "request_timeout_seconds": 65,
            "drain_seconds_max": 70,
            "verdict_scope": "Complete diagnostic gate, transport verdict retained separately",
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
        if refresh_mode == NORMAL:
            from test_worker_capacity_comparison import owned_redis, process_tree, wait_for_log

            assert owned_redis().dbsize() == 0, "Owned Redis database must be empty"
            celery_events = artifact_folder / "celery-events-raw"
            celery_events.mkdir(mode=0o700)
            environment["WEB_MODELOS_CELERY_OBSERVER_DIR"] = str(celery_events)
            environment["WEB_MODELOS_PROCESS_ROLE"] = "web"
            commands = {
                "worker": [sys.executable, "-m", "celery", "-A", "config", "worker", "--loglevel=INFO",
                           "--concurrency=2"],
                "beat": [sys.executable, "-m", "celery", "-A", "config", "beat", "--loglevel=INFO",
                         "--schedule", str(tmp_path / "celerybeat-schedule")],
            }
            for role, command in commands.items():
                with (artifact_folder / f"celery-{role}.log").open("w") as log:
                    celery_processes[role] = subprocess.Popen(
                        command, env={**environment, "WEB_MODELOS_PROCESS_ROLE": role},
                        stdout=log, stderr=log, start_new_session=True)
            ready = time.monotonic() + 60
            wait_for_log(artifact_folder / "celery-worker.log", " ready.", celery_processes["worker"], ready)
            wait_for_log(artifact_folder / "celery-beat.log", "beat: Starting", celery_processes["beat"], ready)
            summary["celery_pids"] = {role: process_tree(p.pid) for role, p in celery_processes.items()}
            sampler = PublicationSampler(artifact_folder / "publication-samples.jsonl", db)
            sampler.start()
        with logfile.open("w") as output:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    *observer_args,
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
        # The fixture's bulk_create bypasses model signals and this harness runs no refresh
        # worker or Beat: repeat the MOD-05 deployment step so the arrivals meet the
        # deployed configuration, where the worker keeps stored state current.
        prepare_output = io.StringIO()
        call_command("refresh_publication_state", stdout=prepare_output)
        dataset["deployment_step_after_fixture"] = prepare_output.getvalue().strip()
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
        if refresh_mode == NORMAL:
            from test_worker_capacity_comparison import BEAT_PHASE_SECONDS, beat_refresh_publishes

            # Same rule as the 4/6 comparison: arrivals start 5 s after an observed Beat tick.
            beat_deadline = time.monotonic() + 45
            while not (ticks := beat_refresh_publishes(celery_events)):
                assert time.monotonic() < beat_deadline, "No Beat refresh observed before load"
                time.sleep(0.2)
            target = ticks[-1] + BEAT_PHASE_SECONDS
            while target < time.monotonic() + 1:
                target += 30
            summary["beat_alignment"] = {"observed_tick_monotonic": ticks[-1], "load_start_target": target,
                                         "phase_seconds": BEAT_PHASE_SECONDS}
            # Persist the existing schedule before waiting, so external diagnostics
            # can attach without adding hooks/imports or warmup inside the workers.
            (artifact_folder / "benchmark-arrival-alignment.json").write_text(json.dumps({
                "run": artifact_folder.name, **summary["beat_alignment"],
                "recorded_monotonic": time.monotonic(),
            }))
            time.sleep(target - time.monotonic())
            summary["dirty_before_load"] = PublicationDirty.objects.count()
            summary["celery_cpu_ticks_before"] = cpu_ticks(
                [pid for pids in summary["celery_pids"].values() for pid in pids])
            sampler.phase = "arrivals_and_drain"
        summary["client_gc_preparation"] = prepare_generator_gc()
        assert summary["client_gc_preparation"]["policy_before"] == summary["client_gc_preparation"]["policy_after"]
        with GCObserver(monotonic_clock=time.monotonic) as client_gc:
            outcome = run_async_open_loop(
                concurrent_fetch,
                routes,
                duration=summary["duration_seconds"],
                rps=summary["arrival_rps"],
                upload_specs=upload_specs,
            )
        summary["client_gc"] = client_gc.report()
        if refresh_mode == NORMAL:
            summary["celery_cpu_ticks_after"] = cpu_ticks(
                [pid for pids in summary["celery_pids"].values() for pid in pids])
            summary["clock_ticks_per_second"] = os.sysconf("SC_CLK_TCK")
            sampler.phase = "idle_after"
        assert summary["client_gc_preparation"]["completed_at_monotonic"] <= outcome["monotonic_origin_seconds"]
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
            summary["transport_verdict"] = summary["verdict"]
            summary["diagnostic_checks"] = {
                "validity": summary["transport_verdict"] != "INVALID",
                "latency_and_errors": summary["transport_verdict"] == "PASS",
                "pending_at_window": summary["window_close"]["dynamic"]["pending"] <= 20,
                "final_pending": summary["counts"]["pending"] == 0,
                "upload": summary["final_upload_counts"]["successful"] == upload_count,
                "timeout_policy": manifest["policy"]["request_timeout_seconds"] == 65,
                "drain": summary["actual_elapsed_seconds"] <= (
                    manifest["duration_seconds"] + manifest["diagnostic_criteria"]["drain_seconds_max"]
                ),
            }
            summary["diagnostic_continue_contract"] = all(summary["diagnostic_checks"].values())
            summary["verdict"] = (
                "INVALID" if summary["transport_verdict"] == "INVALID" else
                "PASS" if summary["diagnostic_continue_contract"] else "FAIL"
            )
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
        if sampler:
            sampler.close()
        for role, owned in celery_processes.items():
            if owned.poll() is None:
                os.killpg(owned.pid, signal_module.SIGTERM)
            try:
                owned.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(owned.pid, signal_module.SIGKILL)
                owned.wait(timeout=5)
            summary[f"celery_{role}_stopped"] = owned.poll() is not None
        if refresh_mode == NORMAL:
            from test_worker_capacity_comparison import owned_redis

            summary["celery_pid_absence"] = {
                str(pid): not Path(f"/proc/{pid}").exists()
                for pids in summary.get("celery_pids", {}).values() for pid in pids}
            broker = owned_redis()
            keys = list(broker.scan_iter(count=1000))
            if keys:
                broker.delete(*keys)
            summary["owned_redis_keys_removed"] = len(keys)
            summary["owned_redis_empty"] = broker.dbsize() == 0
        if observe_workers:
            observed = collect_events(observer_folder)
            observer_path = artifact_folder / "benchmark-worker-events.json"
            observer_path.write_text(json.dumps(observed, indent=2))
            summary["worker_observer_artifact"] = observer_path.name
            summary["worker_observer_parse_errors"] = observed["parse_errors"]
            summary["not_measured"] = [
                item for item in summary["not_measured"] if item not in ["app/DB CPU", "CPU/request"]
            ] + ["DB CPU; whole-app/other-thread CPU; unobserved request CPU",
                 "causal worker observer overhead; exact TCP/socket queue time",
                 "SQL rows_returned/affected/scanned; normalized dominant SQL patterns during load"]
        if logfile.exists():
            import re

            summary["startup_error_types"] = re.findall(r"([A-Za-z]+Error):", logfile.read_text())[
                -10:
            ]
        summary["cold_probes"] = cold
        if accessfile.exists():
            from scripts.benchmark_server_samples import parse_service_samples

            server_lines = accessfile.read_text().splitlines()
            retained = parse_service_samples(server_lines)
            service_path = artifact_folder / "benchmark-server-service.json"
            service_path.write_text(json.dumps(retained, indent=2))
            summary["gunicorn_service_artifact"] = service_path.name
            summary["gunicorn_service_parse_errors"] = retained["parse_errors"]
            server_rows = [line.split() for line in server_lines]
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
