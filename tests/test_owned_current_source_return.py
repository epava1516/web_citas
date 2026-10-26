"""One real current/previous/current source-process return, without image builds."""

import hashlib
import io
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path, PurePosixPath

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.test import Client
from test_owned_interactive_rights_profile import _files, _snapshot_digest, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)
CURRENT, PREVIOUS = "0dcf89f", "8589acd"


def _tree(commit):
    rows = {}
    for line in subprocess.check_output(["git", "ls-tree", "-r", "-z", commit]).decode().split("\0"):
        if not line:
            continue
        meta, name = line.split("\t", 1)
        if name.startswith(("docs/", "tests/", ".ai/")):
            continue
        mode, kind, blob = meta.split()
        assert kind == "blob" and mode in {"100644", "100755"}
        rows[name] = {"mode": mode, "blob": blob}
    return rows


def _export(commit, rows, target):
    target.mkdir(mode=0o700)
    body = subprocess.check_output(["git", "archive", "--format=tar", commit, "--", *rows])
    assert len(body) < 32 * 1024 * 1024
    seen, total = set(), 0
    with tarfile.open(fileobj=io.BytesIO(body), mode="r:") as archive:
        for entry in archive:
            relative = PurePosixPath(entry.name)
            assert not relative.is_absolute() and ".." not in relative.parts
            destination = target.joinpath(*relative.parts)
            assert destination.resolve().is_relative_to(target.resolve())
            if entry.isdir():
                destination.mkdir(mode=0o700, parents=True, exist_ok=True)
                continue
            assert entry.isfile() and entry.name in rows and entry.name not in seen
            data = archive.extractfile(entry).read()
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            assert blob == rows[entry.name]["blob"]
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(data)
            destination.chmod(0o600)
            seen.add(entry.name)
            total += len(data)
    assert seen == set(rows)
    return total


def _private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(text)


def _migrations():
    with connection.cursor() as cursor:
        cursor.execute("SELECT app,name,applied FROM django_migrations ORDER BY app,name")
        return hashlib.sha256(repr(cursor.fetchall()).encode()).hexdigest()


def _phase(source, helper, database, settings, cookie, target_name, target_pk, expected_receiver):
    helper.mkdir(mode=0o700)
    admin_path = source / "apps/core/admin.py"
    expected_hash = hashlib.sha256(admin_path.read_bytes()).hexdigest()
    _private(helper / "owned_return_settings.py",
             "from config.settings import *\nDATABASES = " + repr({"default": database})
             + "\nSECRET_KEY = " + repr(settings.SECRET_KEY)
             + "\nSECRET_KEY_FALLBACKS = " + repr(list(settings.SECRET_KEY_FALLBACKS))
             + "\nMEDIA_ROOT = " + repr(str(settings.MEDIA_ROOT)) + "\n")
    _private(helper / "owned_return_wsgi.py",
             "import hashlib,json,os\nfrom pathlib import Path\n"
             "from config.wsgi import application\nfrom apps.core import admin\n"
             "p=Path(admin.__file__).resolve()\n"
             + "assert p == Path(" + repr(str(admin_path.resolve())) + ")\n"
             + "assert hashlib.sha256(p.read_bytes()).hexdigest() == " + repr(expected_hash) + "\n"
             + "assert hasattr(admin,'bind_admin_login_epoch') is " + repr(expected_receiver) + "\n"
             + "out=Path(" + repr(str(helper.resolve())) + ")/('source-'+str(os.getpid())+'.json')\n"
             + "out.write_text(json.dumps({'source_sha256':" + repr(expected_hash)
             + ",'receiver_present':" + repr(expected_receiver) + "}))\n")
    environment = dict(os.environ, DJANGO_SETTINGS_MODULE="owned_return_settings",
                       APP_ENV="development", DJANGO_DEBUG="0",
                       PYTHONPATH=str(helper) + os.pathsep + str(source))
    environment.pop("GUNICORN_CMD_ARGS", None)
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    process, children, ready, samples = None, set(), set(), []
    log = helper / "gunicorn.log"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with log.open("w") as output:
            began = time.perf_counter()
            process = subprocess.Popen(
                [sys.executable, "-m", "gunicorn", "owned_return_wsgi:application",
                 "--config", str(source / "gunicorn.conf.py"),
                 "--bind", "127.0.0.1:" + str(port), "--workers", "4",
                 "--worker-class", "sync", "--threads", "1", "--timeout", "60",
                 "--access-logfile", "-", "--error-logfile", "-"],
                cwd=source, env=environment, stdout=output, stderr=output, start_new_session=True)
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                text = log.read_text()
                children = set(map(int, re.findall(r"Booting worker with pid: (\d+)", text)))
                ready = set(map(int, re.findall(r"Static routes and templates prepared for worker pid=(\d+)", text)))
                assert process.poll() is None, "Owned source-return Gunicorn exited before readiness"
                if len(ready) == 4:
                    break
                time.sleep(.05)
            startup = time.perf_counter() - began
            assert ready == children and len(ready) == 4
            for pid in ready:
                loaded = json.loads((helper / ("source-" + str(pid) + ".json")).read_text())
                assert loaded == {"source_sha256": expected_hash, "receiver_present": expected_receiver}
            paths = [("health", "/health/", {}),
                     ("authorized_group_read", f"/en/admin/auth/group/{target_pk}/change/",
                      {"Cookie": settings.SESSION_COOKIE_NAME + "=" + cookie})]
            for label, path, headers in paths:
                began = time.perf_counter()
                request = urllib.request.Request("http://127.0.0.1:" + str(port) + path, headers=headers)
                with opener.open(request, timeout=5) as response:
                    body = response.read(1024 * 1024)
                    status, final_path = response.status, response.url
                    cache = response.headers.get("Cache-Control", "")
                elapsed = time.perf_counter() - began
                assert status == 200 and final_path.endswith(path)
                if label == "health":
                    assert json.loads(body) == {"status": "ok"}
                else:
                    assert target_name.encode() in body and "no-store" in cache
                samples.append({"label": label, "http_status": status,
                                "seconds": elapsed, "body_bytes": len(body)})
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
    return {"source_admin_sha256": expected_hash, "receiver_present": expected_receiver,
            "four_actual_sources_verified": True, "ready_workers": len(ready),
            "spawn_to_ready_observed_seconds": startup, "readiness_poll_seconds": .05,
            "samples": samples, "master_exit": process.returncode, "children_absent": True}


def test_current_previous_current_owned_source_process_return(request, settings, tmp_path, record_property):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial source-process return only")
    assert not os.environ.get("PYTEST_XDIST_WORKER") and not settings.PRODUCTION and not settings.RECOVERY_MODE
    database = _owned_database()
    request.getfixturevalue("directory")
    actor = User.objects.get(username="fixture-v1-moderator")
    assert actor.is_active and actor.email_verified_at and actor.mfa_enabled and not actor.is_superuser
    actor.is_staff, actor.session_version = True, 1
    actor.save(update_fields=["is_staff", "session_version"])
    actor.user_permissions.add(*Permission.objects.filter(content_type__app_label="auth",
                                                          codename__in=["view_group", "change_group"]))
    client = Client()
    client.force_login(actor)
    session = client.session
    session["account_version"], session["mfa_version"] = 1, actor.mfa_version
    session.save()
    group = Group.objects.create(name="synthetic-owned-return-group")
    current, previous = _tree(CURRENT), _tree(PREVIOUS)
    assert set(current) == set(previous) and len(current) == 753
    assert [p for p in current if current[p] != previous[p]] == ["apps/core/admin.py"]
    roots = {key: tmp_path / key for key in ["current", "previous"]}
    exported = {"current": _export(CURRENT, current, roots["current"]),
                "previous": _export(PREVIOUS, previous, roots["previous"])}
    database = {key: database[key] for key in ["ENGINE", "NAME", "USER", "PASSWORD", "HOST", "PORT",
                                              "OPTIONS", "CONN_MAX_AGE", "CONN_HEALTH_CHECKS"]}
    before, files, migrations = _state(), _files(settings), _migrations()
    phases = []
    for index, key in enumerate(["current", "previous", "current"]):
        phase = _phase(roots[key], tmp_path / ("phase-" + str(index)), database, settings,
                       session.session_key, group.name, group.pk, key == "current")
        assert _snapshot_digest(_state()) == _snapshot_digest(before)
        assert _files(settings) == files and _migrations() == migrations
        phase.update(source_phase=key, exact_all_rows_files_and_migrations_unchanged=True)
        phases.append(phase)
    record_property("n10f_current_source_return", json.dumps({
        "current_product": CURRENT, "previous_target": PREVIOUS, "runtime_paths": len(current),
        "runtime_delta": ["apps/core/admin.py"], "exported_source_bytes": exported,
        "phases": phases, "installed_models": len(before), "media_files": files["count"],
        "scope": "Actual current/previous/current owned four-sync-worker Gunicorn source-process "
                 "switches, same disposable PostgreSQL and admitted synthetic session. No image "
                 "build/switch, deploy, writes during return, native login/TOTP ceremony, worker/Beat "
                 "mix, provider, zero-downtime or SLA claim. Previous source lacks epoch1 native "
                 "Admin login fix; controlled-maintenance read continuity only. Every exported "
                 "runtime file bound to Git blob; no docs/tests/.ai or venv copies.",
    }, sort_keys=True))
