"""Owned real Celery worker/Beat processes consume synthetic expiry and bump jobs."""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from celery import Celery
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup

from apps.catalog.promotion_order_models import PromotionBumpExecution
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Person, User
from apps.listings.models import LifecycleAction, Listing

pytestmark = pytest.mark.django_db(transaction=True)


def test_real_worker_and_beat_expire_and_bump_without_changing_editorial_state(
    request, settings, tmp_path
):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id, "Use run_local_ci.py with --isolate-test-broker for this owned runtime proof"
    output = Path("artifacts/local-ci") / run_id
    assert json.loads((output / "runner.json").read_text())["id"] == run_id
    assert connection.settings_dict["NAME"].startswith("test_") and not settings.PRODUCTION
    user, listing, version, credentials = setup(request, settings)
    version.product.kind = "autobump"
    version.product.save(update_fields=["kind"])
    # Declared fixture product configuration, before the immutable order snapshot.
    version.bump_interval_minutes, version.daily_bump_limit = 1440, 1
    version.save(update_fields=["bump_interval_minutes", "daily_bump_limit"])
    order = create_order(user, listing.pk, version.pk, uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
    receive_event(user, payload, signature, **credentials)
    entitlement = order.entitlement
    entitlement.starts_at = timezone.now() - timedelta(days=2)
    entitlement.ends_at = entitlement.starts_at + timedelta(days=order.duration_days)
    entitlement.save(update_fields=["starts_at", "ends_at"])
    assert entitlement.ends_at - entitlement.starts_at == timedelta(days=order.duration_days)
    before = (listing.published_at, listing.expires_at, listing.lifecycle_version,
              listing.approved_revision_id, listing.revisions.count())
    victim = Person.objects.get(subject__username="fixture-v1-model-a").listing
    Listing.objects.filter(pk=victim.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

    queue = "beta-exposure-" + uuid4().hex
    module = "beta_exposure_runtime_" + uuid4().hex
    runtime = tmp_path / (module + ".py")
    runtime.write_text(
        "import importlib, os\n"
        "_base = importlib.import_module(os.environ['BETA_EXPOSURE_PARENT_SETTINGS'])\n"
        "globals().update({k: getattr(_base, k) for k in dir(_base) if k.isupper()})\n"
        "CELERY_TASK_ALWAYS_EAGER = False\n"
        "CELERY_TASK_EAGER_PROPAGATES = False\n"
        "PROMOTION_TEST_MODE = True\n"
        f"CELERY_TASK_DEFAULT_QUEUE = {queue!r}\n"
        "CELERY_BEAT_SCHEDULE = {\n"
        " 'probe-expiry': {'task': 'apps.listings.tasks.expire_listings', 'schedule': 1.0},\n"
        " 'probe-bump': {'task': 'apps.catalog.tasks.bump_promotions', 'schedule': 1.0},\n"
        "}\n"
    )
    env = os.environ.copy()
    env.update(
        POSTGRES_DB=connection.settings_dict["NAME"],
        BETA_EXPOSURE_PARENT_SETTINGS=env["DJANGO_SETTINGS_MODULE"],
        DJANGO_SETTINGS_MODULE=module,
        PYTHONPATH=str(tmp_path) + os.pathsep + env.get("PYTHONPATH", ""),
        PROMOTION_TEST_MODE="1",
    )
    publisher = Celery("beta-exposure-publisher", broker=settings.CELERY_BROKER_URL,
                       set_as_current=False)
    publisher.conf.broker_transport_options = dict(settings.CELERY_BROKER_TRANSPORT_OPTIONS)
    publisher.conf.task_ignore_result = True
    processes, logs, jobs = [], [], []
    proof = {"result": "ERROR", "run_id": run_id, "queue": queue,
             "settings_sha256": hashlib.sha256(runtime.read_bytes()).hexdigest(),
             "synthetic_only": True, "real_worker_and_beat": True,
             "synthetic_entitlement_duration_days": order.duration_days,
             "simulated_identity_and_payment": True}

    def start(label, arguments):
        path = tmp_path / (label + ".log")
        stream = path.open("w")
        logs.append((label, path, stream))
        process = subprocess.Popen(
            [sys.executable, "-m", "celery", "-A", "config", *arguments],
            env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True,
        )
        processes.append((label, process))
        return path

    def wait_for(predicate, reason):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            assert all(p.poll() is None for _, p in processes), "Owned runtime process exited"
            if predicate():
                return
            time.sleep(0.1)
        pytest.fail(reason)

    try:
        worker_log = start("worker", [
            "worker", "--loglevel=INFO", "--pool=solo", "--concurrency=1",
            "--without-gossip", "--without-mingle", "-Q", queue,
            "--hostname", queue + "@localhost", "--pidfile", str(tmp_path / "worker.pid"),
        ])
        for task in ["apps.listings.tasks.expire_listings", "apps.catalog.tasks.bump_promotions"]:
            for _ in range(2):
                jobs.append(publisher.send_task(task, queue=queue).id)
        wait_for(
            lambda: all("[" + job + "] succeeded" in worker_log.read_text() for job in jobs),
            "Owned worker did not complete all four dispatched jobs",
        )
        victim.refresh_from_db()
        assert victim.status == "expired"
        assert LifecycleAction.objects.filter(listing=victim, operation="expire", actor=None).count() == 1
        initial_windows = list(PromotionBumpExecution.objects.filter(entitlement=entitlement)
                               .order_by("window_start"))
        assert 1 <= len(initial_windows) <= 2
        assert len(initial_windows) == len({item.window_start.date() for item in initial_windows})
        initial = initial_windows[0]
        entitlement.refresh_from_db()
        checked = entitlement.last_checked_at
        assert checked is not None and entitlement.last_bumped_at is not None
        proof["worker_job_ids"] = jobs
        proof["worker_expiry_events"] = 1
        proof["worker_bump_executions"] = len(initial_windows)

        # A new synthetic expiry proves Beat dispatch, not an earlier explicit job.
        subject = User.objects.create_user(username="beat-expiry-" + uuid4().hex)
        person = Person.objects.create(individual=subject, subject=subject, alias="Synthetic Beat expiry")
        beat_victim = Listing.objects.create(
            person=person, status="published", expires_at=timezone.now() - timedelta(seconds=1)
        )  # No approved revision: never publicly eligible.
        start("beat", ["beat", "--loglevel=INFO", "--schedule", str(tmp_path / "beat-state"),
                       "--pidfile", str(tmp_path / "beat.pid")])

        def beat_completed():
            beat_victim.refresh_from_db()
            entitlement.refresh_from_db()
            return (beat_victim.status == "expired" and entitlement.last_checked_at > checked)

        wait_for(beat_completed, "Owned Beat did not dispatch both expiry and bump checks")
        assert LifecycleAction.objects.filter(listing=beat_victim, operation="expire", actor=None).count() == 1
        assert LifecycleAction.objects.filter(listing=victim, operation="expire", actor=None).count() == 1
        # UTC midnight may legitimately open the next daily window during the probe.
        assert PromotionBumpExecution.objects.filter(
            entitlement=entitlement, window_start=initial.window_start
        ).count() == 1
        windows = list(PromotionBumpExecution.objects.filter(entitlement=entitlement)
                       .order_by("window_start").values_list("window_start", flat=True))
        assert len(windows) == len({window.date() for window in windows})
        listing.refresh_from_db()
        assert (listing.published_at, listing.expires_at, listing.lifecycle_version,
                listing.approved_revision_id, listing.revisions.count()) == before
        proof.update(result="PASS", beat_expiry_events=1, beat_rechecked=True,
                     bump_windows=[w.isoformat() for w in windows], editorial_state_unchanged=True)
    finally:
        publisher.close()
        for _, process in reversed(processes):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
        proof["processes"] = [{"role": label, "pid": p.pid, "exit": p.returncode,
                               "terminated": p.poll() is not None} for label, p in processes]
        for label, path, stream in logs:
            stream.close()
            target = output / ("beta-exposure-" + label + ".log")
            shutil.copyfile(path, target)
            proof[label + "_log_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        (output / "beta-exposure-worker-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    assert all(item["terminated"] for item in proof["processes"])
