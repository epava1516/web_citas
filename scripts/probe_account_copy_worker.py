"""Isolated PostgreSQL/Redis/Celery/Beat probe of account copy snapshot expiry.

Synthetic task fixtures only: no identity approval, email delivery or account change.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from datetime import timedelta


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["launch", "worker", "beat", "fixture", "state", "dispatch"]
    )
    parser.add_argument("--queue", default="")
    parser.add_argument("--task-id", default="")
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    assert not settings.PRODUCTION, "Synthetic operational probe prohibited in production"
    if options.mode == "launch":
        return launch(settings)
    database = settings.DATABASES["default"]["NAME"]
    assert database.startswith("account_copy_probe_"), "Isolated database required"
    assert settings.RIGHTS_VERIFICATION_BACKEND == settings.SAFETY_NOTICE_BACKEND == "disabled"
    assert settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND == "disabled"
    from config.celery import app

    settings.CELERY_RESULT_BACKEND = settings.CELERY_BROKER_URL
    settings.CELERY_TASK_IGNORE_RESULT = False
    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    if options.mode in {"worker", "beat", "dispatch"}:
        assert options.queue == database, "Isolated queue required"
        assert not app.conf.task_always_eager
    if options.mode == "worker":
        return app.worker_main(
            ["worker", "--loglevel=INFO", "--concurrency=1", "-Q", options.queue]
        )
    if options.mode == "beat":
        app.conf.task_default_queue = options.queue
        # Keep the actual application's task and interval; isolate unrelated schedules.
        app.conf.beat_schedule = {
            "purge-expired-private-copies": settings.CELERY_BEAT_SCHEDULE[
                "purge-expired-private-copies"
            ]
        }
        return app.Beat(loglevel="INFO", schedule="/tmp/account-copy-probe-beat").run()
    if options.mode == "fixture":
        fixture()
    elif options.mode == "dispatch":
        from apps.safety.tasks import purge_expired_exports

        job = purge_expired_exports.apply_async(queue=options.queue, ignore_result=False)
        print(json.dumps({"task_id": job.id}), flush=True)
    else:
        state(app, options.task_id)


def fixture():
    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import User
    from apps.safety.crypto import seal
    from apps.safety.models import (
        RightsAction,
        RightsExport,
        RightsExportDownload,
        RightsProof,
        RightsRequest,
    )
    from apps.safety.rights import fingerprint

    marker, now = uuid.uuid4().hex, timezone.now()
    with transaction.atomic():
        user = User.objects.create_user(
            username="ops-copy-" + marker, email=marker + "@example.invalid"
        )
        case = RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest=fingerprint(marker),
            payload_digest=fingerprint(marker),
            encrypted_payload=seal({"synthetic_task_fixture": True}),
            kind="access",
            account_subject=user,
            reported_subject=user,
            received_at=now,
            initial_due_at=now + timedelta(days=1),
            receipt_expires_at=now + timedelta(days=1),
        )
        proof = RightsProof.objects.create(
            key=uuid.uuid4(),
            request=case,
            account_subject=user,
            initiated_by=user,
            case_version=1,
            manager_version=None,
            subject_id_snapshot=str(user.pk),
            scope="access",
            account_source_digest=fingerprint(marker),
            channel_digest=case.receipt_digest,
            provider="simulator",
            procedure="rights-simulator-v1",
            payload_digest=fingerprint(marker),
            encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            expires_at=now + timedelta(hours=1),
        )
        for expired in (True, False):
            action = RightsAction.objects.create(
                key=uuid.uuid4(),
                request=case,
                actor=user,
                expected_version=1,
                operation="export",
                payload_digest=fingerprint(marker + str(expired)),
                encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            )
            export = RightsExport.objects.create(
                action=action,
                proof=proof,
                account_subject=user,
                manager_version=None,
                case_version=1,
                subject_snapshot=str(user.pk),
                channel_digest=case.receipt_digest,
                encrypted_payload=seal({"synthetic_task_fixture": True, "marker": marker}),
                expires_at=now + timedelta(seconds=-1 if expired else 86400),
            )
            RightsExportDownload.objects.create(key=uuid.uuid4(), export=export)
    print(
        json.dumps(
            {"fixture_created": True, "identity_approved": False, "external_delivery": False}
        ),
        flush=True,
    )


def state(app, task_id):
    from django.utils import timezone

    from apps.core.models import Person, User
    from apps.safety.models import (
        RightsAction,
        RightsExport,
        RightsExportDownload,
        RightsProof,
        RightsRequest,
    )

    expired = RightsExport.objects.filter(expires_at__lte=timezone.now()).order_by("pk")
    live = RightsExport.objects.filter(expires_at__gt=timezone.now()).order_by("pk")
    metadata = [
        field.attname
        for field in RightsExport._meta.concrete_fields
        if field.name not in {"encrypted_payload", "purged_at"}
    ]
    preserved = [
        list(model.objects.order_by("pk").values())
        for model in (User, Person, RightsAction, RightsProof, RightsRequest, RightsExportDownload)
    ]
    preserved.append(list(RightsExport.objects.order_by("pk").values(*metadata)))
    preserved.append(list(live.values("pk", "encrypted_payload", "purged_at")))
    data = {
        "expired": expired.count(),
        "purged": expired.filter(encrypted_payload="", purged_at__isnull=False).count(),
        "live": live.count(),
        "live_content_preserved": not live.filter(encrypted_payload="").exists()
        and not live.filter(purged_at__isnull=False).exists(),
        "preservation_digest": hashlib.sha256(
            json.dumps(preserved, sort_keys=True, default=str).encode()
        ).hexdigest(),
        "purge_dates": list(expired.values_list("pk", "purged_at")),
        "actions": RightsAction.objects.count(),
        "proofs": RightsProof.objects.count(),
        "downloads": RightsExportDownload.objects.count(),
        "users": User.objects.count(),
        "people": Person.objects.count(),
    }
    if task_id:
        job = app.AsyncResult(task_id)
        data["task"] = {
            "id": job.id,
            "status": job.status,
            "result": job.result if job.successful() else None,
        }
    print(json.dumps(data, default=str), flush=True)


def wait(prefix, expired, task_id="", timeout=40):
    deadline = time.monotonic() + timeout
    result = {}
    while time.monotonic() < deadline:
        args = ["state"] + (["--task-id", task_id] if task_id else [])
        result = json.loads(command(prefix + args))
        if result["expired"] == result["purged"] == expired and (
            not task_id or result["task"]["status"] == "SUCCESS"
        ):
            assert result["live"] == expired and result["live_content_preserved"]
            assert result["users"] == result["proofs"] == expired
            assert result["actions"] == result["downloads"] == expired * 2
            assert result["people"] == 0
            return result
        time.sleep(1)
    print(json.dumps({"probe_timeout_state": result}), flush=True)
    raise AssertionError("Account copy worker or Beat did not reach expected state")


def launch(settings):
    import psycopg
    from psycopg import sql

    config = json.loads(command(["docker", "compose", "config", "--format", "json"]))
    assert config["services"]["worker"]["environment"].get("APP_ENV", "development") != "production"
    database = "account_copy_probe_" + uuid.uuid4().hex[:12]
    worker, beat = database + "_worker", database + "_beat"
    db = settings.DATABASES["default"]
    connection = psycopg.connect(
        dbname="postgres",
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        autocommit=True,
    )
    connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    env_args = [
        "-e",
        "POSTGRES_DB=" + database,
        "-e",
        "SAFETY_NOTICE_BACKEND=disabled",
        "-e",
        "RIGHTS_VERIFICATION_BACKEND=disabled",
        "-e",
        "CELERY_TASK_ALWAYS_EAGER=0",
        "-e",
        "ACCOUNT_CORRECTION_DELIVERY_BACKEND=disabled",
    ]
    prefix = ["docker", "exec", worker, "python", "-m", "scripts.probe_account_copy_worker"]
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
                *env_args,
                "worker",
                "python",
                "-m",
                "scripts.probe_account_copy_worker",
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        before = json.loads(command(prefix + ["state"]))
        started = time.monotonic()
        job = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        first = wait(prefix, 1, job)
        assert (
            first["task"]["result"] == 1
            and first["preservation_digest"] == before["preservation_digest"]
        )
        repeat = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        second = wait(prefix, 1, repeat)
        assert (
            second["task"]["result"] == 0
            and first["purge_dates"] == second["purge_dates"]
            and first["preservation_digest"] == second["preservation_digest"]
        )
        print(
            json.dumps(
                {
                    "worker_passed": True,
                    "task_ids": [job, repeat],
                    "expired_export_payloads_removed": 1,
                    "live_ciphertext_and_source_rows_preserved": True,
                    "audit_preserved": True,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
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
                *env_args,
                "beat",
                "python",
                "-m",
                "scripts.probe_account_copy_worker",
                "beat",
                "--queue",
                database,
            ]
        )
        started = time.monotonic()
        final = wait(prefix, 2, timeout=85)
        assert final["preservation_digest"] == before_beat["preservation_digest"]
        assert (
            final["purge_dates"][0] == second["purge_dates"][0]
            or final["purge_dates"][1] == second["purge_dates"][0]
        )
        beat_log = subprocess.run(
            ["docker", "logs", beat], capture_output=True, text=True, check=True
        )
        assert "purge-expired-private-copies" in beat_log.stdout + beat_log.stderr
        worker_log = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        text = worker_log.stdout + worker_log.stderr
        received = set(
            re.findall(
                r"Task apps\.safety\.tasks\.purge_expired_exports\[([a-f0-9-]+)\] received",
                text,
            )
        )
        succeeded = set(
            re.findall(
                r"Task apps\.safety\.tasks\.purge_expired_exports\[([a-f0-9-]+)\] succeeded",
                text,
            )
        )
        automatic = succeeded - {job, repeat}
        assert {job, repeat} <= received & succeeded and automatic and automatic <= received
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "manual_dispatch_for_beat": False,
                    "automatic_task_ids": sorted(automatic),
                    "expired_export_payloads_removed": 2,
                    "live_export_payloads_preserved": 2,
                    "audit_preserved": True,
                    "account_changes_performed": False,
                    "identity_verified": False,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "isolated_database": database,
                }
            ),
            flush=True,
        )
    finally:
        subprocess.run(["docker", "rm", "-f", beat], capture_output=True)
        subprocess.run(
            ["docker", "exec", worker, "celery", "-A", "config", "purge", "-Q", database, "-f"],
            capture_output=True,
        )
        subprocess.run(["docker", "rm", "-f", worker], capture_output=True)
        connection.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
        )
        connection.close()
        print(
            "Isolated synthetic database and containers removed; application data preserved",
            flush=True,
        )


if __name__ == "__main__":
    main()
