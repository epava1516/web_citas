"""Owned test worker for real Celery retry/failure/success event delivery."""
import argparse
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection  # noqa: E402

from config.celery import app  # noqa: E402


@app.task(bind=True, name="operational_probe.retry_failure", max_retries=1)
def retry_failure(self, private_argument):
    assert connection.settings_dict["NAME"].startswith("test_")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
    if not self.request.retries:
        raise self.retry(exc=RuntimeError("SYNTHETIC_PRIVATE_FAILURE"), countdown=0)
    raise RuntimeError("SYNTHETIC_PRIVATE_FAILURE")


@app.task(name="operational_probe.success")
def success(private_argument):
    assert connection.settings_dict["NAME"].startswith("test_")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
    return {"private_result": private_argument}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    options = parser.parse_args()
    assert options.queue.startswith("operational_probe_")
    assert connection.settings_dict["NAME"].startswith("test_")
    app.worker_main(["worker", "--pool=solo", "--concurrency=1", "--loglevel=INFO",
                     "--without-gossip", "--without-mingle", "--without-heartbeat",
                     "-Q", options.queue, "--hostname", options.queue + "@local"])


if __name__ == "__main__":
    main()
