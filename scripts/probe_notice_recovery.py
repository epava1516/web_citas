"""Owned prefork worker: inject one simulator failure, never a provider call."""
import argparse
import os
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402

from apps.safety import notice_delivery  # noqa: E402
from config.celery import app  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--failure-marker", type=Path, required=True)
    options = parser.parse_args()
    if not connection.settings_dict["NAME"].startswith("test_"):
        raise RuntimeError("Probe requires an isolated test database")
    if settings.PRODUCTION or settings.SAFETY_NOTICE_BACKEND != "simulator":
        raise RuntimeError("Probe requires the local simulator")
    if not options.queue.startswith("notice_recovery_probe_"):
        raise RuntimeError("Probe requires its own queue")
    marker = options.failure_marker.resolve()
    if not marker.parent.is_dir() or marker.exists():
        raise RuntimeError("Probe requires a fresh marker in an existing owned directory")
    original = notice_delivery.simulated_adapter

    def fail_once(notice):
        try:
            descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return original(notice)
        else:
            os.close(descriptor)
            raise RuntimeError("Synthetic local adapter interruption")

    # Inherited by the owned prefork children only; application modules stay unchanged.
    notice_delivery.simulated_adapter = fail_once
    app.worker_main([
        "worker", "--pool=prefork", "--concurrency=2", "--loglevel=INFO",
        "--without-gossip", "--without-mingle", "--without-heartbeat",
        "-Q", options.queue, "--hostname", options.queue + "@local",
    ])


if __name__ == "__main__":
    main()
