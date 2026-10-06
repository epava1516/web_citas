"""Synthetic actual-worker probe; no providers, messages or business writes."""

import argparse
import json
import os
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection  # noqa: E402

from config.celery import app  # noqa: E402


@app.task(name="recovery_gate.synthetic_database_probe")
def database_probe():
    assert connection.settings_dict["NAME"].startswith("test_")
    marker = Path(os.environ["RECOVERY_PROBE_MARKER"])
    assert marker.parent.stat().st_mode & 0o077 == 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_backend_pid()")
        pid = cursor.fetchone()[0]
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump({"synthetic_probe_executed": True, "postgres_pid": pid}, output)
    return {"synthetic_probe_executed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--beat", action="store_true")
    parser.add_argument("--schedule")
    options = parser.parse_args()
    assert options.queue.startswith("recovery_gate_")
    if options.beat:
        from django.conf import settings

        assert options.schedule
        if settings.RECOVERY_MODE:
            assert not app.conf.beat_schedule
        else:
            app.conf.update(
                CELERY_BEAT_SCHEDULE={
                    "synthetic-probe": {
                        "task": "recovery_gate.synthetic_database_probe",
                        "schedule": 0.5,
                        "options": {"queue": options.queue},
                    }
                }
            )
        print(
            json.dumps(
                {"effective_tasks": [entry["task"] for entry in app.conf.beat_schedule.values()]}
            ),
            flush=True,
        )
        return app.Beat(loglevel="INFO", schedule=options.schedule, max_interval=0.2).run()
    app.worker_main(
        [
            "worker",
            "--pool=solo",
            "--concurrency=1",
            "--loglevel=INFO",
            "--without-gossip",
            "--without-mingle",
            "--without-heartbeat",
            "-Q",
            options.queue,
            "--hostname",
            options.queue + "@local",
        ]
    )


if __name__ == "__main__":
    main()
