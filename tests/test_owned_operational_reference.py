"""Finite N10 references: real local startup and positive aggregate CLI output."""

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from io import StringIO
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.core.management import call_command
from django.db import connection
from test_owned_interactive_rights_profile import _files, _snapshot_digest, _state

pytestmark = pytest.mark.django_db(transaction=True)


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL operational reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    _owned_database()


def _unchanged(before, media_before, settings):
    after = _state()
    assert _snapshot_digest(before) == _snapshot_digest(after)
    assert _files(settings) == media_before
    return {"models_including_through": len(before), "rows_unchanged": True,
            "media_unchanged": True, "media_files": media_before["count"]}


def test_current_four_worker_startup(request, settings, tmp_path, record_property):
    _guard(request, settings)
    settings.MEDIA_ROOT = str(tmp_path / "media")
    before, media_before = _state(), _files(settings)
    module = tmp_path / "n10_startup_settings.py"
    module.write_text(
        'from config.settings import *\nDATABASES["default"]["NAME"] = '
        + repr(connection.settings_dict["NAME"])
        + '\nMEDIA_ROOT = ' + repr(settings.MEDIA_ROOT) + '\n', encoding="utf-8")
    environment = dict(os.environ, DJANGO_SETTINGS_MODULE="n10_startup_settings",
                       APP_ENV="development", DJANGO_DEBUG="0",
                       PYTHONPATH=str(tmp_path) + os.pathsep + str(Path.cwd()))
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    logfile = tmp_path / "gunicorn.log"
    process, children, ready, samples = None, set(), set(), []
    startup_seconds = None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with logfile.open("w", encoding="utf-8") as output:
            started = time.perf_counter()
            process = subprocess.Popen(
                [sys.executable, "-m", "gunicorn", "config.wsgi:application",
                 "--bind", "127.0.0.1:" + str(port), "--workers", "4", "--timeout", "60",
                 "--access-logfile", "-", "--error-logfile", "-"],
                env=environment, stdout=output, stderr=output, start_new_session=True)
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                text = logfile.read_text(encoding="utf-8")
                children = set(map(int, re.findall(r"Booting worker with pid: (\d+)", text)))
                ready = set(map(int, re.findall(
                    r"Static routes and templates prepared for worker pid=(\d+)", text)))
                assert process.poll() is None, "Owned Gunicorn exited before readiness"
                if len(ready) == 4:
                    startup_seconds = time.perf_counter() - started
                    break
                time.sleep(.05)
            assert len(ready) == 4 and ready == children
            for index in range(6):
                started = time.perf_counter()
                with opener.open("http://127.0.0.1:" + str(port) + "/health/", timeout=5) as response:
                    body = response.read(1024)
                    status = response.status
                elapsed = time.perf_counter() - started
                assert status == 200 and json.loads(body) == {"status": "ok"}
                samples.append({"sample": index, "http_status": status,
                                "seconds": elapsed, "response_bytes": len(body)})
            assert process.poll() is None
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            deadline = time.monotonic() + 5
            while any(Path("/proc", str(pid)).exists() for pid in children) and time.monotonic() < deadline:
                time.sleep(.05)
            assert not any(Path("/proc", str(pid)).exists() for pid in children)
    assert process is not None and process.returncode == 0
    oracle = _unchanged(before, media_before, settings)
    record_property("n10b_startup", json.dumps({
        "spawn_to_four_ready_observed_seconds": startup_seconds,
        "readiness_poll_seconds": .05, "ready_workers": len(ready),
        "health_samples": samples, "master_exit": process.returncode,
        "children_absent": True, "oracle": oracle,
        "scope": "Four actual sync Gunicorn workers; current root config; own disposable "
                 "PG migrator credentials. Readiness log detection includes polling. Six "
                 "sequential local health TCP requests; no worker affinity, SQL count, "
                 "capacity, least privilege, provider or deployment SLA claim.",
    }, sort_keys=True))


def test_positive_snapshot_cli_reference(request, settings, tmp_path, record_property):
    _guard(request, settings)
    settings.MEDIA_ROOT = str(tmp_path / "media")
    before, media_before = _state(), _files(settings)
    observations, stable = [], None
    for index in range(6):
        output = StringIO()
        totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

        def observe(execute, sql, params, many, context):
            totals["sql_queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                totals["sql_execute_seconds"] += time.perf_counter() - started

        started = time.perf_counter()
        with connection.execute_wrapper(observe):
            call_command("operational_snapshot", stdout=output, no_color=True)
        elapsed = time.perf_counter() - started
        body = output.getvalue()
        result = json.loads(body)
        assert result["schema_version"] == 1
        assert result["scope"] == "durable_database_work_only"
        assert result["publication"] == {"count": 0, "oldest_age_seconds": None}
        assert "worker_liveness" in result["not_measured"]
        assert result["object_storage"]["orphan_inventory"] == "unmeasured"
        assert body.endswith("\n") and len(body.splitlines()) == 1
        sampled_at = result.pop("sampled_at")
        assert isinstance(sampled_at, str) and sampled_at
        if stable is None:
            stable = result
        else:
            assert result == stable
        assert connection.get_autocommit() and not connection.in_atomic_block
        observations.append({"sample": index, "phase": "first" if index == 0 else "warm",
                             "cli_in_process_seconds_instrumented": elapsed,
                             "stdout_bytes": len(body.encode()), **totals})
    oracle = _unchanged(before, media_before, settings)
    record_property("n10b_snapshot_cli", json.dumps({
        "samples": observations, "oracle": oracle, "json_schema": 1,
        "scope": "Six in-process call_command invocations: command dispatch, collector "
                 "and JSON serialization; database work tables empty. First invocation "
                 "separate from five warm samples; no Python spawn, worker liveness, "
                 "backlog scaling or provider claim. Earlier collector 0/10/100 reused.",
    }, sort_keys=True))
