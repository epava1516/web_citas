"""Real isolated PostgreSQL/Redis/worker/Beat purge; synthetic ledger, no identity claims."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from datetime import timedelta
from pathlib import Path

TASKS = {"drafts": "apps.safety.tasks.purge_expired_access_response_drafts"}


def command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        artifact = Path("/tmp") / ("fdprobe-command-" + uuid.uuid4().hex + ".log")
        descriptor = os.open(artifact, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(result.stdout + result.stderr)
        raise RuntimeError("Isolated probe command failed; private diagnostic " + str(artifact))
    return result.stdout.strip()


def fixture():
    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import User
    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction, RightsRequest, RightsResponse
    from apps.safety.rights_final_response import _digest

    now, marker = timezone.now(), uuid.uuid4().hex
    with transaction.atomic():
        actor = User.objects.create_user(
            username="fdprobe-" + marker, email=marker + "@example.invalid"
        )
        for kind, prefix in [
            ("erase", "erase"),
            ("restriction", "process"),
            ("rectify", "rectify"),
        ]:
            case = RightsRequest.objects.create(
                submission_key=uuid.uuid4(),
                kind=kind,
                account_subject=actor,
                received_at=now,
                initial_due_at=now + timedelta(days=1),
                receipt_expires_at=now + timedelta(days=1),
            )
            for index, label in enumerate(["expired", "live", "issued", "legacy"], 1):
                body = {"synthetic_retention_fixture": marker, "class": label}
                draft = RightsAction.objects.create(
                    key=uuid.uuid4(),
                    request=case,
                    actor=actor,
                    expected_version=1,
                    operation=prefix + "_final_draft",
                    payload_digest=_digest(body),
                    encrypted_reason=seal(body),
                )
                RightsAction.objects.filter(pk=draft.pk).update(
                    created_at=now - timedelta(hours=1 if label == "live" else 25)
                )
                if label in {"issued", "legacy"}:
                    key = uuid.uuid4()
                    response = RightsResponse.objects.create(
                        key=key,
                        request=case,
                        actor=actor,
                        case_version=1,
                        response_version=index,
                        kind="progress",
                        payload_digest=draft.payload_digest,
                        encrypted_reason=seal({"synthetic_retention_fixture": True}),
                        encrypted_response=seal(body),
                    )
                    record = {"draft": draft.pk, "draft_digest": draft.payload_digest}
                    RightsAction.objects.create(
                        key=key,
                        request=case,
                        actor=actor,
                        expected_version=1,
                        operation=prefix
                        + ("_final_close" if prefix == "rectify" else "_final_issue"),
                        payload_digest=_digest(record),
                        encrypted_reason=seal(record),
                    )
                    if label == "issued":
                        draft.final_response = response
                        draft.save(update_fields=["final_response"])
    print(json.dumps({"synthetic_ledger_only": True, "identity_verified": False}), flush=True)


def state(app, jobs):
    from apps.core.models import User
    from apps.safety.crypto import unseal
    from apps.safety.models import RightsAction, RightsRequest, RightsResponse

    rows = list(RightsAction.objects.filter(operation__endswith="_final_draft").order_by("pk"))
    expired, purged, live, protected = 0, 0, [], []
    preserved = []
    for row in rows:
        label = unseal(row.encrypted_reason).get("class") if row.encrypted_reason else "expired"
        metadata = {
            field.attname: getattr(row, field.attname)
            for field in row._meta.concrete_fields
            if field.name not in {"encrypted_reason", "purged_at", "final_response"}
        }
        preserved.append(metadata)
        if label == "expired":
            expired += 1
            purged += int(not row.encrypted_reason and row.purged_at is not None)
        else:
            preserved.append(
                {"id": row.pk, "ciphertext": row.encrypted_reason, "purged_at": row.purged_at}
            )
            if label == "live":
                live.append(
                    bool(row.encrypted_reason)
                    and row.purged_at is None
                    and row.final_response_id is None
                )
            else:
                protected.append(
                    bool(row.encrypted_reason)
                    and row.purged_at is None
                    and (row.final_response_id is not None or label == "legacy")
                )
    for model in [User, RightsRequest, RightsResponse]:
        preserved.append(list(model.objects.order_by("pk").values()))
    preserved.append(
        list(
            RightsAction.objects.exclude(operation__endswith="_final_draft").order_by("pk").values()
        )
    )
    print(
        json.dumps(
            {
                "drafts": {
                    "expired": expired,
                    "purged": purged,
                    "live": len(live),
                    "live_preserved": all(live) and all(protected),
                    "protected": len(protected),
                    "protected_linked": sum(row.final_response_id is not None for row in rows),
                    "purge_dates": [(row.pk, row.purged_at) for row in rows if row.purged_at],
                },
                "preservation_digest": hashlib.sha256(
                    json.dumps(preserved, sort_keys=True, default=str).encode()
                ).hexdigest(),
                "jobs": {
                    label: {
                        "status": app.AsyncResult(job).status,
                        "result": app.AsyncResult(job).result
                        if app.AsyncResult(job).successful()
                        else None,
                    }
                    for label, job in jobs.items()
                },
            },
            default=str,
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["launch", "worker", "beat", "fixture", "state", "dispatch"]
    )
    parser.add_argument("--queue", default="")
    parser.add_argument("--jobs", default="{}")
    args = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    assert not settings.PRODUCTION
    if args.mode == "launch":
        return launch(settings)
    database = settings.DATABASES["default"]["NAME"]
    assert database.startswith("fdprobe_")
    assert settings.RIGHTS_VERIFICATION_BACKEND == settings.SAFETY_NOTICE_BACKEND == "disabled"
    from config.celery import app

    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    app.conf.update(CELERY_TASK_DEFAULT_QUEUE=database)
    assert app.conf.task_default_queue == database
    assert not app.conf.task_always_eager
    if args.mode == "worker":
        assert args.queue == database
        return app.worker_main(["worker", "--loglevel=INFO", "--concurrency=1", "-Q", database])
    if args.mode == "beat":
        assert args.queue == database
        app.conf.task_default_queue = database
        selected_schedule = {
            "purge-expired-access-response-drafts": settings.CELERY_BEAT_SCHEDULE[
                "purge-expired-access-response-drafts"
            ]
        }
        # The Django CELERY namespace takes precedence over lower-case updates.
        app.conf.update(CELERY_BEAT_SCHEDULE=selected_schedule)
        assert app.conf.beat_schedule == selected_schedule
        assert {entry["task"] for entry in app.conf.beat_schedule.values()} == set(TASKS.values())
        return app.Beat(loglevel="INFO", schedule="/tmp/final-draft-probe-beat").run()
    if args.mode == "fixture":
        return fixture()
    if args.mode == "dispatch":
        assert args.queue == database
        print(
            json.dumps(
                {
                    label: app.send_task(task, queue=database, ignore_result=False).id
                    for label, task in TASKS.items()
                }
            ),
            flush=True,
        )
    else:
        state(app, json.loads(args.jobs))


def launch(settings):
    import psycopg
    from psycopg import sql

    database = "fdprobe_" + uuid.uuid4().hex[:12]
    worker, beat = database + "_worker", database + "_beat"
    db = settings.DATABASES["default"]
    conn = psycopg.connect(
        dbname="postgres",
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        autocommit=True,
    )
    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    env = [
        "-e",
        "POSTGRES_DB=" + database,
        "-e",
        "TASK_QUEUE_GENERATION=" + database.replace("_", ""),
        "-e",
        "RIGHTS_VERIFICATION_BACKEND=disabled",
        "-e",
        "SAFETY_NOTICE_BACKEND=disabled",
        "-e",
        "ACCOUNT_CORRECTION_DELIVERY_BACKEND=disabled",
        "-e",
        "CELERY_TASK_ALWAYS_EAGER=0",
        "-v",
        str(Path(__file__).resolve()) + ":/app/probe_final_draft.py:ro",
    ]
    prefix = ["docker", "exec", worker, "python", "/app/probe_final_draft.py"]

    def wait(count, jobs=None, timeout=45):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            data = json.loads(command(prefix + ["state", "--jobs", json.dumps(jobs or {})]))
            if all(
                data[label]["expired"] == data[label]["purged"] == count * 3 for label in TASKS
            ) and all(row["status"] == "SUCCESS" for row in data["jobs"].values()):
                assert all(
                    data[label]["live"] == count * 3 and data[label]["live_preserved"]
                    for label in TASKS
                )
                assert data["drafts"]["protected_linked"] == count * 6
                return data
            time.sleep(1)
        raise AssertionError("Final draft retention probe timeout")

    try:
        command(
            [
                "docker",
                "compose",
                "run",
                "-d",
                "--no-deps",
                "--name",
                worker,
                *env,
                "worker",
                "python",
                "/app/probe_final_draft.py",
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        before = json.loads(command(prefix + ["state"]))
        jobs = json.loads(command(prefix + ["dispatch", "--queue", database]))
        first = wait(1, jobs)
        assert first["preservation_digest"] == before["preservation_digest"]
        assert all(row["result"] == 3 for row in first["jobs"].values())
        repeat = json.loads(command(prefix + ["dispatch", "--queue", database]))
        second = wait(1, repeat)
        assert second["preservation_digest"] == first["preservation_digest"]
        assert all(row["result"] == 0 for row in second["jobs"].values())
        assert all(second[label]["purge_dates"] == first[label]["purge_dates"] for label in TASKS)
        print(
            json.dumps(
                {
                    "worker_passed": True,
                    "jobs": jobs,
                    "repeat": repeat,
                    "audit_and_live_content_preserved": True,
                }
            ),
            flush=True,
        )
        command(prefix + ["fixture"])
        before_beat = json.loads(command(prefix + ["state"]))
        command(
            [
                "docker",
                "compose",
                "run",
                "-d",
                "--no-deps",
                "--name",
                beat,
                *env,
                "beat",
                "python",
                "/app/probe_final_draft.py",
                "beat",
                "--queue",
                database,
            ]
        )
        final = wait(2, timeout=90)
        assert final["preservation_digest"] == before_beat["preservation_digest"]
        logs = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        text = logs.stdout + logs.stderr
        automatic = {}
        for label, task in TASKS.items():
            received = set(
                re.findall(r"Task " + re.escape(task) + r"\[([a-f0-9-]+)\] received", text)
            )
            succeeded = set(
                re.findall(r"Task " + re.escape(task) + r"\[([a-f0-9-]+)\] succeeded", text)
            )
            automatic[label] = sorted(succeeded - {jobs[label], repeat[label]})
            assert automatic[label] and set(automatic[label]) <= received
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "automatic_jobs": automatic,
                    "manual_dispatch_for_beat": False,
                    "preservation_digest": final["preservation_digest"],
                    "isolated_database": database,
                    "identity_verified": False,
                }
            ),
            flush=True,
        )
    except Exception:
        logs = subprocess.run(["docker", "logs", worker], capture_output=True, text=True)
        artifact = Path("/tmp") / (database + ".failure.log")
        descriptor = os.open(artifact, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(logs.stdout + logs.stderr)
        print(json.dumps({"private_worker_diagnostic": str(artifact)}), flush=True)
        print(json.dumps({"probe_failed": True, "raw_logs_not_disclosed": True}), flush=True)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", beat], capture_output=True)
        subprocess.run(
            ["docker", "exec", worker, "celery", "-A", "config", "purge", "-Q", database, "-f"],
            capture_output=True,
        )
        subprocess.run(["docker", "rm", "-f", worker], capture_output=True)
        conn.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
        conn.close()
        print(json.dumps({"isolated_database_and_containers_removed": True}), flush=True)


if __name__ == "__main__":
    main()
