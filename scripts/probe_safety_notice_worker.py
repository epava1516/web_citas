"""Isolated PostgreSQL/Redis/Celery/Beat probe. Never sends to a real channel."""

import argparse
import json
import os
import subprocess
import time
import uuid


def command(args):
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["launch", "fixture", "dispatch", "state", "beat", "worker"]
    )
    parser.add_argument("--queue", default="")
    parser.add_argument("--task-id", action="append", default=[])
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    assert not settings.PRODUCTION, "Synthetic probe prohibited in production"
    if options.mode == "launch":
        return launch(settings)
    assert settings.DATABASES["default"]["NAME"].startswith("notice_probe_"), (
        "Isolated probe database required"
    )
    assert settings.SAFETY_NOTICE_BACKEND == "simulator"
    from config.celery import app

    settings.CELERY_RESULT_BACKEND = settings.CELERY_BROKER_URL
    settings.CELERY_TASK_IGNORE_RESULT = False
    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    if options.mode == "worker":
        assert options.queue.startswith("notice_probe_")
        return app.worker_main(
            ["worker", "--loglevel=INFO", "--concurrency=1", "-Q", options.queue]
        )
    if options.mode == "beat":
        assert options.queue.startswith("notice_probe_")
        app.conf.task_default_queue = options.queue
        return app.Beat(loglevel="INFO", schedule="/tmp/notice-probe-beat").run()
    if options.mode == "dispatch":
        from apps.safety.tasks import deliver_safety_notices

        assert not app.conf.task_always_eager and options.queue.startswith("notice_probe_")
        job = deliver_safety_notices.apply_async(queue=options.queue, ignore_result=False)
        print(json.dumps({"task_id": job.id}), flush=True)
    elif options.mode == "fixture":
        fixture()
    else:
        from apps.safety.models import (
            ComplaintNotice,
            ReportNotice,
            RightsNotice,
            SimulatedComplaintNoticeDelivery,
            SimulatedNoticeDelivery,
            SimulatedRightsNoticeDelivery,
        )

        jobs = [app.AsyncResult(key) for key in options.task_id]
        print(
            json.dumps(
                {
                    "simulated": SimulatedComplaintNoticeDelivery.objects.count()
                    + SimulatedNoticeDelivery.objects.count()
                    + SimulatedRightsNoticeDelivery.objects.count(),
                    "attempts": list(ComplaintNotice.objects.values_list("attempts", flat=True))
                    + list(ReportNotice.objects.values_list("attempts", flat=True))
                    + list(RightsNotice.objects.values_list("attempts", flat=True)),
                    "tasks": [
                        {
                            "id": job.id,
                            "status": job.status,
                            "result": job.result if job.successful() else None,
                        }
                        for job in jobs
                    ],
                }
            ),
            flush=True,
        )


def fixture():
    from datetime import timedelta

    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import User
    from apps.safety.crypto import seal
    from apps.safety.models import (
        Complaint,
        ComplaintAction,
        ComplaintNotice,
        ComplaintResolution,
        Report,
        ReportNotice,
        RightsNotice,
        RightsRequest,
        RightsResponse,
    )

    with transaction.atomic():
        marker = uuid.uuid4().hex
        actor = User.objects.create_user(
            username="notice-probe-" + marker, email=marker + "@example.invalid"
        )
        complaint = Complaint.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest="0" * 64,
            payload_digest="0" * 64,
            encrypted_payload=seal({"synthetic_only": True}),
            status="resolved",
            receipt_expires_at=timezone.now() + timedelta(days=1),
        )
        action = ComplaintAction.objects.create(
            key=uuid.uuid4(),
            complaint=complaint,
            actor=actor,
            expected_version=1,
            operation="resolve",
            payload_digest="0" * 64,
            encrypted_reason=seal({"reason": "Synthetic task fixture; not a real decision"}),
        )
        resolution = ComplaintResolution.objects.create(
            complaint=complaint,
            action=action,
            outcome="upheld",
            encrypted_response=seal({"response": "Synthetic operational fixture only"}),
        )
        payload = seal(
            {
                "recipient": "operational-probe@example.invalid",
                "subject": "Synthetic notice",
                "body": "Operational fixture, no real delivery",
            }
        )
        ComplaintNotice.objects.create(resolution=resolution, encrypted_payload=payload)
        report = Report.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest="0" * 64,
            payload_digest="0" * 64,
            encrypted_payload=seal({"synthetic_only": True}),
            mode="general",
            reason="other",
            receipt_expires_at=timezone.now() + timedelta(days=1),
        )
        ReportNotice.objects.create(
            event_key="probe:" + marker, report=report, kind="ack", encrypted_payload=payload
        )
        now = timezone.now()
        rights = RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest="0" * 64,
            payload_digest="0" * 64,
            encrypted_payload=seal({"synthetic_only": True}),
            kind="access",
            response_version=1,
            received_at=now,
            initial_due_at=now + timedelta(days=1),
            receipt_expires_at=now + timedelta(days=1),
        )
        response = RightsResponse.objects.create(
            key=uuid.uuid4(),
            request=rights,
            actor=actor,
            case_version=1,
            response_version=1,
            kind="progress",
            payload_digest="0" * 64,
            encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            encrypted_response=seal({"text": "Synthetic task fixture only", "simulation": True}),
        )
        RightsNotice.objects.create(response=response, encrypted_payload=payload)
    print(json.dumps({"synthetic_notices_created": 3, "identity_verified": False}), flush=True)


def launch(settings):
    import psycopg
    from psycopg import sql

    config = json.loads(command(["docker", "compose", "config", "--format", "json"]))
    assert config["services"]["worker"]["environment"].get("APP_ENV", "development") != "production"
    marker = uuid.uuid4().hex[:12]
    database = "notice_probe_" + marker
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
        "SAFETY_NOTICE_BACKEND=simulator",
        "-e",
        "CELERY_TASK_ALWAYS_EAGER=0",
    ]
    prefix = ["docker", "exec", worker, "python", "-m", "scripts.probe_safety_notice_worker"]
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
                "scripts.probe_safety_notice_worker",
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        job = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        started = time.monotonic()
        state = wait(prefix, simulated=3, task_id=job)
        assert state["tasks"][0]["result"]["simulated"] == 3
        repeat = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        state = wait(prefix, simulated=3, task_id=repeat)
        assert state["tasks"][0]["result"]["processed"] == 0
        print(
            json.dumps(
                {
                    "worker_passed": True,
                    "task_ids": [job, repeat],
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
            ),
            flush=True,
        )
        command(prefix + ["fixture"])
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
                "scripts.probe_safety_notice_worker",
                "beat",
                "--queue",
                database,
            ]
        )
        started = time.monotonic()
        state = wait(prefix, simulated=6, timeout=85)
        assert state["attempts"] == [1, 1, 1, 1, 1, 1]
        beat_output = subprocess.run(
            ["docker", "logs", beat], capture_output=True, text=True, check=True
        )
        worker_output = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        beat_log = beat_output.stdout + beat_output.stderr
        worker_log = worker_output.stdout + worker_output.stderr
        assert "deliver-private-safety-notices" in beat_log
        assert job in worker_log and repeat in worker_log and "succeeded" in worker_log
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "manual_dispatch_for_beat": False,
                    "simulated_records": 6,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "real_channel_used": False,
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
            "Isolated synthetic database and containers removed; application records preserved",
            flush=True,
        )


def wait(prefix, simulated, task_id=None, timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        args = ["state"] + (["--task-id", task_id] if task_id else [])
        state = json.loads(command(prefix + args))
        if state["simulated"] == simulated and (
            not task_id or state["tasks"][0]["status"] == "SUCCESS"
        ):
            return state
        time.sleep(1)
    print(json.dumps({"probe_timeout_state": state}), flush=True)
    raise AssertionError("Notice worker or Beat probe did not reach expected state")


if __name__ == "__main__":
    main()
