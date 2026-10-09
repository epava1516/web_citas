"""Explicitly authorized, sequential 4/6/6/4 experiment; never a load gate."""
import hashlib
import http.cookies
import io
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote
from uuid import uuid4

import psycopg
import pytest
from django.conf import settings as django_settings
from django.core import signing
from django.core.management import call_command
from django.db import connection
from django.test import Client
from psycopg import sql
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Listing, PublicationDirty, Revision
from scripts.benchmark_async_transport import POLICY, fetch_http, run_async_open_loop
from scripts.benchmark_gc_observer import GCObserver, generator_gc_overlap, prepare_generator_gc
from scripts.benchmark_publication_sampler import PublicationSampler
from scripts.benchmark_resource_probe import ResourceProbe
from scripts.benchmark_worker_observer import collect_events
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

# Refresh scenarios. The first is the configuration of every previous load harness: no
# Celery worker or Beat; tasks run eagerly inside the web process when a model signal
# schedules them, and signal-less writes (e.g. the final Photo update of image processing)
# leave marks that nothing refreshes. The second is the deployed MOD05 topology.
EAGER = "without_worker_beat_eager_signal"
NORMAL = "normal_worker_beat"
OWNED_REDIS = "redis://127.0.0.1:56379/15"
# Owned runtime settings load the task observer only when its output is set; process
# commands stay identical to compose.yaml.
OBSERVER_SETTINGS = ('import os as _os\nif _os.environ.get("WEB_MODELOS_CELERY_OBSERVER_DIR"):\n'
                     '    import scripts.benchmark_celery_observer  # noqa: F401,E402\n')


def owned_redis():
    import redis

    return redis.Redis.from_url(OWNED_REDIS)


def process_tree(root):
    """PIDs of root and its live descendants, from /proc."""
    parents = {}
    for item in Path("/proc").iterdir():
        if item.name.isdigit():
            try:
                stat = (item / "stat").read_text()
            except OSError:
                continue
            parents[int(item.name)] = int(stat.rsplit(")", 1)[1].split()[1])
    tree, frontier = {root}, [root]
    while frontier:
        current = frontier.pop()
        for pid, ppid in parents.items():
            if ppid == current and pid not in tree:
                tree.add(pid)
                frontier.append(pid)
    return sorted(tree)


BEAT_PHASE_SECONDS = 5


def beat_refresh_publishes(folder):
    ticks = []
    for path in folder.glob("celery-beat-*.jsonl"):
        for line in path.read_text().splitlines():
            event = json.loads(line)
            if event["event"] == "publish" and event["task"].endswith("refresh_publication_state"):
                ticks.append(event["monotonic"])
    return sorted(ticks)


def wait_for_log(path, marker, process, deadline):
    while marker not in (path.read_text() if path.exists() else ""):
        assert process.poll() is None, f"Owned process exited before {marker!r}"
        assert time.monotonic() < deadline, f"Owned process readiness timeout: {marker!r}"
        time.sleep(.1)


def terminate_owned(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


@pytest.mark.skipif(not os.getenv("WORKER_COMPARISON_OUTPUT"), reason="Explicit authorized owned experiment only")
def test_worker_capacity_comparison(request, tmp_path, record_property):
    request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    dataset = populate(10000)
    db = dict(connection.settings_dict)
    assert db["NAME"].startswith("test_promotion_gate_")
    out = Path(os.environ["WORKER_COMPARISON_OUTPUT"])
    manifest = json.loads((out / "frozen-manifest.json").read_text())
    limits = manifest["limits"]
    # Identical private upload and fixture identities in each fresh clone.
    manager = User.objects.get(username="fixture-v1-individual")
    person = Person.objects.get(individual=manager)
    draft = Revision.objects.create(listing=person.listing, manager_version=person.manager_version)
    client = Client()
    client.force_login(manager)
    session_cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value
    # MOD05: clone the same officially prepared state after creating the upload
    # draft/session. The timed upload may mark it again; native fallback stays on.
    deployment_output = io.StringIO()
    call_command("refresh_publication_state", stdout=deployment_output)
    assert not PublicationDirty.objects.exists()
    dataset["deployment_step"] = deployment_output.getvalue().strip()
    raw = raw_image(782134)
    boundary = "synthetic-fixed-worker-comparison"
    multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="synthetic.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
                 + raw + f"\r\n--{boundary}--\r\n".encode())
    routes = ["/es/", "/en/", "/es/?q=photography", "/en/?q=synthetic",
              "/es/listing/" + dataset["sample_ids"][0] + "/",
              "/en/listing/" + dataset["sample_ids"][-1] + "/"]
    detail_targets = {str(row.pk): {"listing": str(row.pk), "revision": str(row.approved_revision_id)}
                      for row in Listing.objects.filter(pk__in=[dataset["sample_ids"][0], dataset["sample_ids"][-1]])}
    with connection.cursor() as cursor:
        cursor.execute("ANALYZE")
        cursor.execute("SHOW server_version")
        pg_version = cursor.fetchone()[0]
        cursor.execute("""SELECT table_name,column_name,data_type,udt_name,is_nullable,column_default
                          FROM information_schema.columns WHERE table_schema='public'
                          ORDER BY table_name,ordinal_position""")
        columns = cursor.fetchall()
        cursor.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname")
        indexes = cursor.fetchall()
        cursor.execute("SELECT app,name FROM django_migrations ORDER BY app,name")
        migrations = cursor.fetchall()
    (out / "schema-fingerprint.json").write_text(json.dumps({"columns": columns, "indexes": indexes,
        "migrations": migrations, "sha256": hashlib.sha256(json.dumps([columns,indexes,migrations],sort_keys=True).encode()).hexdigest()}, indent=2))
    connection.close()
    pg_pid = int(subprocess.check_output(["docker", "inspect", "--format", "{{.State.Pid}}", "web-modelos-db-1"], text=True).strip())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    body_hashes, reports, last_upload = {}, [], None
    admin_args = dict(dbname=os.environ["POSTGRES_DB"], user=db["USER"], password=db["PASSWORD"],
                      host=db["HOST"], port=db["PORT"], autocommit=True)
    with psycopg.connect(**admin_args) as admin:
        orders = manifest.get("orders", [4, 6, 6, 4])
        assert orders in ([4], [4, 6, 6, 4]), "Only explicitly recorded closed scenarios"
        refresh_mode = manifest.get("refresh_mode", EAGER)
        assert refresh_mode in (EAGER, NORMAL), "Only recorded refresh scenarios"
        for index, workers in enumerate(orders):
            folder = out / f"block-{index+1}-{workers}w"
            folder.mkdir(mode=0o700)
            name = "test_promotion_gate_workers_" + uuid4().hex[:16]
            names = json.loads((out / "owned-databases.json").read_text())
            (out / "owned-databases.json").write_text(json.dumps(names + [name]))
            admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(name), sql.Identifier(db["NAME"])))
            runtime = tmp_path / f"runtime-{index}"
            runtime.mkdir()
            media = runtime / "private"
            shutil.copytree(django_settings.MEDIA_ROOT, media)
            runtime_settings = "from config.settings import *\nMEDIA_ROOT = " + repr(str(media)) + "\n"
            if refresh_mode == EAGER:
                runtime_settings += ('CELERY_TASK_ALWAYS_EAGER = True\nCELERY_TASK_EAGER_PROPAGATES = True\n'
                                     'CELERY_BEAT_SCHEDULE = {}\nCELERY_RESULT_BACKEND = "cache+memory://"\n')
            # NORMAL keeps the deployed Celery configuration and Beat schedule unchanged;
            # only the broker is an owned, empty Redis database with an owned key prefix.
            (runtime / "load_runtime_settings.py").write_text(runtime_settings + OBSERVER_SETTINGS)
            celery_events = folder / "celery-events-raw"
            celery_events.mkdir(mode=0o700)
            observer = folder / "worker-events-raw"
            observer.mkdir(mode=0o700)
            env = os.environ.copy()
            generation = "w" + uuid4().hex[:31]
            env.update(POSTGRES_DB=name, POSTGRES_USER=db["USER"], POSTGRES_PASSWORD=db["PASSWORD"],
                       DB_HOST=db["HOST"], DB_PORT=str(db["PORT"]), APP_ENV="development", DJANGO_DEBUG="0",
                       DJANGO_SETTINGS_MODULE="load_runtime_settings", PYTHONPATH=str(runtime)+os.pathsep+str(Path.cwd()),
                       REDIS_URL="memory://" if refresh_mode == EAGER else OWNED_REDIS,
                       TASK_QUEUE_GENERATION=generation,
                       WEB_MODELOS_BENCHMARK_OBSERVER_DIR=str(observer),
                       WEB_MODELOS_CELERY_OBSERVER_DIR=str(celery_events), WEB_MODELOS_PROCESS_ROLE="web")
            process, probe, sampler, celery_processes = None, None, None, {}
            report = {"index": index+1, "workers": workers, "refresh_mode": refresh_mode,
                      "task_queue_generation": generation, "routes": routes, "dataset": dataset,
                      "postgres_version": pg_version, "verdict": "INVALID", "completed": False,
                      "upload_body_sha256": hashlib.sha256(multipart).hexdigest(), "policy": dict(POLICY)}
            try:
                if refresh_mode == NORMAL:
                    broker = owned_redis()
                    assert broker.dbsize() == 0, "Owned Redis database must be empty before a block"
                    # Same deployed commands (compose.yaml) in every block; owned and isolated.
                    commands = {
                        "worker": [sys.executable, "-m", "celery", "-A", "config", "worker", "--loglevel=INFO",
                                   "--concurrency=2"],
                        "beat": [sys.executable, "-m", "celery", "-A", "config", "beat", "--loglevel=INFO",
                                 "--schedule", str(runtime / "celerybeat-schedule")],
                    }
                    for role, command in commands.items():
                        with (folder / f"celery-{role}.log").open("w") as log:
                            celery_processes[role] = subprocess.Popen(command, env={**env, "WEB_MODELOS_PROCESS_ROLE": role}, stdout=log,
                                                                      stderr=log, start_new_session=True)
                    ready_deadline = time.monotonic() + 60
                    wait_for_log(folder / "celery-worker.log", " ready.", celery_processes["worker"], ready_deadline)
                    wait_for_log(folder / "celery-beat.log", "beat: Starting", celery_processes["beat"], ready_deadline)
                    report["celery_pids"] = {role: process_tree(p.pid) for role, p in celery_processes.items()}
                with (folder / "gunicorn-private.log").open("w") as log:
                    process = subprocess.Popen([sys.executable, "-m", "gunicorn", "--config", "python:scripts.benchmark_resource_observer",
                        "config.wsgi:application", "--bind", f"127.0.0.1:{port}", "--workers", str(workers), "--timeout", "65",
                        "--access-logfile", str(folder / "gunicorn-access.log"), "--access-logformat", "%(s)s %(L)s %(U)s %({x-benchmark-id}i)s",
                        "--error-logfile", "-", "--graceful-timeout", "10"], env=env, stdout=log, stderr=log, start_new_session=True)
                report["master_pid"] = process.pid
                deadline = time.monotonic()+30
                while True:
                    assert process.poll() is None, "Owned Gunicorn exited during startup"
                    if len(list(observer.glob("worker-*.jsonl"))) == workers:
                        try:
                            with urllib.request.urlopen(origin+"/health/", timeout=1) as response:
                                if response.status == 200:
                                    break
                        except OSError:
                            pass
                    assert time.monotonic() < deadline, "Owned server failed readiness"
                    time.sleep(.1)
                clone_db = {**db, "NAME": name}
                probe = ResourceProbe(folder/"resource-samples.jsonl", clone_db, process.pid, pg_pid, trial_limits=limits)
                probe.start()
                sampler = PublicationSampler(folder/"publication-samples.jsonl", clone_db)
                sampler.start()
                report["resource_affinity"] = {"application": sorted(os.sched_getaffinity(process.pid)), "postgres": sorted(os.sched_getaffinity(pg_pid))}
                time.sleep(5)
                assert not probe.trial_limits.requested.is_set(), "Resource bound during idle"
                probe.phase = sampler.phase = "warmup"
                cold, serial = [], []
                for cycle in range(6):
                    for route_index, path in enumerate(routes):
                        assert not probe.trial_limits.requested.is_set(), "Resource bound during warmup"
                        start = time.monotonic()
                        headers = {} if cycle == 0 else {"X-Benchmark-Id": "d-"+str(2000+(cycle-1)*6+route_index)}
                        with urllib.request.urlopen(urllib.request.Request(origin+path, headers=headers), timeout=65) as response:
                            body = response.read()
                            assert response.status == 200
                        raw_digest = hashlib.sha256(body).hexdigest()
                        if route_index >= 4:
                            # Django TimestampSigner changes this capability each second.
                            # Validate signature, freshness and exact target before replacing
                            # only that volatile token in the comparator, never the response.
                            match = re.search(rb'target=([^&]+)&amp;reference=', body)
                            assert match is not None
                            target = signing.loads(unquote(match[1].decode()), salt="public-report-target-v1", max_age=7200)
                            assert target == detail_targets[path.split("/")[3]]
                            stable = quote(json.dumps(target, sort_keys=True, separators=(",", ":"))).encode()
                            body = body[:match.start(1)] + stable + body[match.end(1):]
                        digest = hashlib.sha256(body).hexdigest()
                        assert body_hashes.setdefault(path, digest) == digest, "Body changed between controls"
                        if route_index < 4:
                            assert re.search(rb"<p>10000 (?:results|resultados)</p>", body)
                        row = {"path": path, "body_sha256": digest, "raw_body_sha256": raw_digest, "signed_target_valid": route_index >= 4, "emitted_monotonic": start, "seconds": time.monotonic()-start}
                        if cycle:
                            row["id"] = headers["X-Benchmark-Id"]
                            serial.append(row)
                        else:
                            cold.append(row)
                report.update(cold_probes=cold, serial_reference=serial, exact_body_hashes=body_hashes.copy())
                cookies = http.cookies.SimpleCookie()
                with urllib.request.urlopen(origin+"/es/account/login/", timeout=65) as response:
                    for value in response.headers.get_all("Set-Cookie", []):
                        cookies.load(value)
                csrf = cookies[django_settings.CSRF_COOKIE_NAME].value
                upload = {"at": 0, "path": f"/es/draft/{draft.pk}/photos/upload/", "data": multipart,
                    "headers": {"Cookie": f"{django_settings.SESSION_COOKIE_NAME}={session_cookie}; {django_settings.CSRF_COOKIE_NAME}={csrf}",
                                "X-CSRFToken": csrf, "Referer": origin+"/es/", "Content-Type": "multipart/form-data; boundary="+boundary}, "expected": 302}
                with psycopg.connect(dbname=name, user=db["USER"], password=db["PASSWORD"], host=db["HOST"],
                                     port=db["PORT"], autocommit=True) as check:
                    report["dirty_before_load"] = check.execute(
                        "SELECT count(*) FROM listings_publicationdirty").fetchone()[0]
                probe.phase = sampler.phase = "upload_spacing"
                if last_upload is not None:
                    time.sleep(max(0, last_upload+60-time.monotonic()))
                if refresh_mode == NORMAL:
                    # Same Beat phase in every block: the load (and its upload at t=0) starts
                    # BEAT_PHASE_SECONDS after an observed Beat publish of the 30 s refresh.
                    beat_deadline = time.monotonic() + 45
                    while not (ticks := beat_refresh_publishes(celery_events)):
                        assert time.monotonic() < beat_deadline, "No Beat refresh observed before load"
                        time.sleep(.2)
                    tick = ticks[-1]
                    target = tick + BEAT_PHASE_SECONDS
                    while target < time.monotonic() + .5:
                        target += 30
                    time.sleep(target - time.monotonic())
                    report["beat_alignment"] = {"observed_tick_monotonic": tick, "load_start_target": target,
                                                "phase_seconds": BEAT_PHASE_SECONDS}
                assert not probe.trial_limits.requested.is_set(), "Resource bound before load"
                report["client_gc_preparation"] = prepare_generator_gc()
                probe.phase = sampler.phase = "arrivals_and_drain"
                async def fetch(path, **kwargs):
                    return await fetch_http(origin, path, timeout_seconds=65, **kwargs)
                with GCObserver(monotonic_clock=time.monotonic) as gc:
                    outcome = run_async_open_loop(fetch, routes, duration=30, rps=20, upload_specs=[upload],
                                                  stop_requested=probe.trial_limits.requested)
                report.update(outcome)
                report["client_gc"] = gc.report()
                report["client_gc_emission_overlap"] = generator_gc_overlap(gc.report()["events"], outcome["samples"], outcome["monotonic_origin_seconds"])
                if outcome["uploads"][0]["emitted_at"] is not None:
                    last_upload = outcome["monotonic_origin_seconds"]+outcome["uploads"][0]["emitted_at"]
                (folder/"benchmark-samples.json").write_text(json.dumps({"dynamic": outcome["samples"], "uploads": outcome["uploads"], "clock": outcome["clock"]}, indent=2))
                assert outcome["counts"]["reconciled"] and outcome["final_upload_counts"]["reconciled"]
                report["completed"] = not outcome["trial_resource_stopped"]
                # Server work may outlive client timeouts. Observe until idle within the same fixed drain bound.
                server_deadline = outcome["monotonic_origin_seconds"]+100
                while time.monotonic() < server_deadline and not probe.trial_limits.requested.is_set():
                    observed = collect_events(observer)
                    starts = {e["id"] for e in observed["events"] if e["event"] == "wsgi_start"}
                    ends = {e["id"] for e in observed["events"] if e["event"] == "wsgi_end"}
                    emitted = {r["id"] for r in outcome["samples"]+outcome["uploads"] if r["emitted_at"] is not None}
                    if emitted <= ends and starts == ends:
                        break
                    time.sleep(.1)
                report["server_cohort_end_monotonic"] = time.monotonic()
                probe.phase = sampler.phase = "idle_after"
                if not probe.trial_limits.requested.is_set():
                    time.sleep(5)
            except Exception as exc:
                report["execution_error_type"] = type(exc).__name__
                raise
            finally:
                if sampler:
                    sampler.close()
                if probe:
                    probe.close()
                    report["trial_stop"] = probe.trial_limits.reason
                terminate_owned(process)
                report["gunicorn_stopped"] = process is None or process.poll() is not None
                for role, owned in celery_processes.items():
                    terminate_owned(owned)
                    report[f"celery_{role}_stopped"] = owned.poll() is not None
                if celery_processes:
                    report["celery_pid_absence"] = {
                        str(pid): not Path(f"/proc/{pid}").exists()
                        for pids in report.get("celery_pids", {}).values() for pid in pids}
                if refresh_mode == NORMAL:
                    broker = owned_redis()
                    owned_keys = list(broker.scan_iter(count=1000))
                    report["owned_redis_keys_removed"] = len(owned_keys)
                    if owned_keys:
                        broker.delete(*owned_keys)
                    report["owned_redis_empty"] = broker.dbsize() == 0
                report["worker_pid_absence"] = {p.stem: not Path("/proc/"+p.stem.split("-")[1]).exists() for p in observer.glob("worker-*.jsonl")}
                (folder/"benchmark-worker-events.json").write_text(json.dumps(collect_events(observer), indent=2))
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
                report["database_absence"] = not admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", [name]).fetchall()
                shutil.rmtree(runtime)
                report["media_absence"] = not runtime.exists()
                report["block_artifact_sha256"] = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob("*") if p.is_file()}
                (folder/"load-summary.json").write_text(json.dumps(report, indent=2))
                reports.append({k:v for k,v in report.items() if k not in ["samples", "serial_reference", "cold_probes", "client_gc"]})
                (out/"blocks-terminal.json").write_text(json.dumps(reports, indent=2))
                print(f"Block {index+1}: {workers} workers terminal, verdict {report['verdict']}", flush=True)
            if report.get("trial_stop") or not report["completed"]:
                break  # Preserve partials; no automated retry or variant after resource stop.
            # Root reviews each terminal block before allowing the already planned next block.
            review_deadline = time.monotonic()+300
            while not (folder/"review-release.json").exists():
                assert time.monotonic() < review_deadline, "Terminal block awaiting independent review"
                time.sleep(.2)
    record_property("capacity_comparison", json.dumps({"blocks": reports, "original_fixture": dataset, "not_a_gate": True}))
