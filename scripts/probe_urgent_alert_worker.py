"""Isolated real worker/Beat probe of internal urgent alerts; no outward messages."""

import argparse
import json
import os
import subprocess
import time
import uuid


def command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        detail = result.stderr[-4000:]
        from django.conf import settings

        for secret in [settings.DATABASES["default"]["PASSWORD"], settings.SECRET_KEY]:
            if secret:
                detail = detail.replace(secret, "[redacted]")
        raise RuntimeError(detail)
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

    assert not settings.PRODUCTION
    if options.mode == "launch":
        return launch(settings)
    assert settings.DATABASES["default"]["NAME"].startswith("alert_probe_")
    assert settings.SAFETY_NOTICE_BACKEND == "disabled"
    from config.celery import app

    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    if options.mode == "worker":
        assert options.queue.startswith("alert_probe_")
        return app.worker_main(
            ["worker", "--loglevel=INFO", "--concurrency=1", "-Q", options.queue]
        )
    if options.mode == "beat":
        assert options.queue.startswith("alert_probe_")
        app.conf.task_default_queue = options.queue
        return app.Beat(loglevel="INFO", schedule="/tmp/alert-probe-beat").run()
    if options.mode == "dispatch":
        from apps.safety.tasks import reconcile_urgent_report_alerts

        assert not app.conf.task_always_eager and options.queue.startswith("alert_probe_")
        job = reconcile_urgent_report_alerts.apply_async(queue=options.queue, ignore_result=False)
        print(json.dumps({"task_id": job.id}), flush=True)
    elif options.mode == "fixture":
        from datetime import timedelta

        from django.utils import timezone

        from apps.safety.models import Report

        Report.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest="0" * 64,
            payload_digest="0" * 64,
            encrypted_payload="synthetic-unused-fixture",
            mode="general",
            reason="minor",
            priority=0,
            receipt_expires_at=timezone.now() + timedelta(days=1),
        )
        print(json.dumps({"synthetic_report_created": True}), flush=True)
    else:
        from apps.safety.models import Report, UrgentReportAlert

        jobs = [app.AsyncResult(key) for key in options.task_id]
        print(
            json.dumps(
                {
                    "alerts": UrgentReportAlert.objects.count(),
                    "acknowledged": UrgentReportAlert.objects.filter(
                        acknowledged_at__isnull=False
                    ).count(),
                    "versions": list(Report.objects.values_list("version", flat=True)),
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


def launch(settings):
    import psycopg
    from psycopg import sql

    config = json.loads(command(["docker", "compose", "config", "--format", "json"]))
    assert config["services"]["worker"]["environment"].get("APP_ENV", "development") != "production"
    marker = uuid.uuid4().hex[:12]
    database = "alert_probe_" + marker
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
        "CELERY_TASK_ALWAYS_EAGER=0",
    ]
    prefix = ["docker", "exec", worker, "python", "-m", "scripts.probe_urgent_alert_worker"]
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
                "scripts.probe_urgent_alert_worker",
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        job = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        started = time.monotonic()
        state = wait(prefix, alerts=1, task_id=job)
        assert state["tasks"][0]["result"]["reconciled"] == 1
        repeat = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        state = wait(prefix, alerts=1, task_id=repeat)
        assert state["tasks"][0]["result"]["reconciled"] == 0
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
                "scripts.probe_urgent_alert_worker",
                "beat",
                "--queue",
                database,
            ]
        )
        started = time.monotonic()
        state = wait(prefix, alerts=2, timeout=85)
        assert state["acknowledged"] == 0 and state["versions"] == [1, 1]
        beat_output = subprocess.run(
            ["docker", "logs", beat], capture_output=True, text=True, check=True
        )
        worker_output = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        beat_log = beat_output.stdout + beat_output.stderr
        worker_log = worker_output.stdout + worker_output.stderr
        assert "reconcile-urgent-report-alerts" in beat_log
        assert job in worker_log and repeat in worker_log and "succeeded" in worker_log
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "manual_dispatch_for_beat": False,
                    "persistent_alerts": 2,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "real_channel_used": False,
                    "isolated_database": database,
                }
            ),
            flush=True,
        )
    except Exception:
        logs = subprocess.run(["docker", "logs", worker], capture_output=True, text=True)
        print((logs.stdout + logs.stderr)[-3000:], flush=True)
        raise
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


def wait(prefix, alerts, task_id=None, timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        args = ["state"] + (["--task-id", task_id] if task_id else [])
        state = json.loads(command(prefix + args))
        if state["alerts"] == alerts and (not task_id or state["tasks"][0]["status"] == "SUCCESS"):
            return state
        time.sleep(1)
    print(json.dumps({"probe_timeout_state": state}), flush=True)
    raise AssertionError("Urgent alert worker or Beat did not reach expected state")


if __name__ == "__main__":
    main()
