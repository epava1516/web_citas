"""Isolated physical media deletion probe; synthetic pending identity, no rights decision."""

import argparse
import hashlib
import io
import json
import os
import subprocess
import time
import uuid
from datetime import timedelta

from scripts.probe_export_retention_worker import command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["launch", "worker", "beat", "fixture", "state", "dispatch", "cleanup"]
    )
    parser.add_argument("--queue", default="")
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    from config.celery import app

    assert not settings.PRODUCTION
    assert settings.MEDIA_STORAGE_PROVIDER == "local"
    if options.mode == "launch":
        return launch(settings)
    database = settings.DATABASES["default"]["NAME"]
    assert database.startswith("media_probe_")
    assert settings.RIGHTS_VERIFICATION_BACKEND == settings.SAFETY_NOTICE_BACKEND == "disabled"
    if options.mode in {"worker", "beat", "dispatch"}:
        assert options.queue == database and not app.conf.task_always_eager
    settings.CELERY_RESULT_BACKEND = settings.CELERY_BROKER_URL
    settings.CELERY_TASK_IGNORE_RESULT = False
    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    if options.mode == "worker":
        return app.worker_main(["worker", "--loglevel=INFO", "--concurrency=1", "-Q", database])
    if options.mode == "beat":
        app.conf.task_default_queue = database
        app.conf.beat_schedule = {
            "erase-private-media": settings.CELERY_BEAT_SCHEDULE["erase-private-media"]
        }
        return app.Beat(loglevel="INFO", schedule="/tmp/media-erasure-probe-beat").run()
    if options.mode == "fixture":
        fixture()
    elif options.mode == "dispatch":
        from apps.mediafiles.tasks import erase_media_files

        task = erase_media_files.apply_async(queue=database, ignore_result=False)
        print(json.dumps({"task_id": task.id}), flush=True)
    else:
        state(cleanup=options.mode == "cleanup")


def fixture():
    from django.conf import settings
    from django.core.files.base import ContentFile
    from django.utils import timezone
    from PIL import Image

    from apps.core.models import Person, User
    from apps.listings.models import Listing, Revision
    from apps.mediafiles.models import Blob, MediaErasure, Photo
    from apps.safety.crypto import seal
    from apps.safety.models import (
        ErasureExecution,
        ErasureInventory,
        ErasurePlan,
        RightsAction,
        RightsProof,
        RightsRequest,
    )

    marker = settings.DATABASES["default"]["NAME"] + "_" + uuid.uuid4().hex
    now = timezone.now()
    image = Image.new("RGB", (32, 32), (14, 59, 126))
    raw, derivative = io.BytesIO(), io.BytesIO()
    image.save(raw, format="PNG")
    image.save(derivative, format="WEBP")
    user = User.objects.create_user(username=marker, email=marker + "@example.invalid")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic task fixture")
    listing = Listing.objects.create(person=person)
    revision = Revision.objects.create(listing=listing, manager_version=1)
    blobs = []
    for index in range(2):
        blob = Blob.objects.create(
            sha256=hashlib.sha256((marker + str(index)).encode()).hexdigest(),
            status="erasing" if index == 0 else "ready",
        )
        blob.original.save(marker + str(index) + ".png", ContentFile(raw.getvalue()), save=False)
        blob.derivative.save(
            marker + str(index) + ".webp", ContentFile(derivative.getvalue()), save=False
        )
        blob.save()
        Photo.objects.create(revision=revision, blob=blob, removed_at=now if index == 0 else None)
        blobs.append(blob)
    paths = {
        "target": [blobs[0].original.name, blobs[0].derivative.name],
        "live": [blobs[1].original.name, blobs[1].derivative.name],
        "live_hashes": [
            hashlib.sha256(raw.getvalue()).hexdigest(),
            hashlib.sha256(derivative.getvalue()).hexdigest(),
        ],
    }
    case = RightsRequest.objects.create(
        submission_key=uuid.uuid4(),
        receipt_digest=marker,
        payload_digest=marker,
        encrypted_payload=seal(paths),
        kind="erase",
        person=person,
        manager_version=1,
        received_at=now,
        initial_due_at=now + timedelta(days=1),
        receipt_expires_at=now + timedelta(days=1),
    )
    proof = RightsProof.objects.create(
        key=uuid.uuid4(),
        request=case,
        person=person,
        initiated_by=user,
        case_version=1,
        manager_version=1,
        scope="erase",
        provider="simulator",
        procedure="rights-simulator-v1",
        payload_digest=marker,
        encrypted_reason=seal({"synthetic_pending": True}),
        expires_at=now + timedelta(hours=1),
    )

    def action(operation):
        return RightsAction.objects.create(
            key=uuid.uuid4(),
            request=case,
            actor=user,
            expected_version=1,
            operation=operation,
            payload_digest=marker,
            encrypted_reason=seal({"synthetic_fixture": True}),
        )

    inventory = ErasureInventory.objects.create(
        action=action("erasure_inventory"),
        proof=proof,
        person=person,
        source_digest=marker,
        encrypted_manifest=seal({"synthetic": True}),
    )
    plan = ErasurePlan.objects.create(
        action=action("erasure_plan"),
        inventory=inventory,
        source_digest=marker,
        encrypted_decisions=seal({"synthetic": True}),
    )
    execution = ErasureExecution.objects.create(
        plan=plan,
        action=action("erasure_execute"),
        proof=proof,
        person=person,
        encrypted_result=seal({"synthetic_task_fixture": True}),
    )
    MediaErasure.objects.create(
        blob=blobs[0],
        execution=execution,
        encrypted_paths=seal({"original": paths["target"][0], "derivative": paths["target"][1]}),
    )


def state(cleanup=False):
    from apps.mediafiles.models import Blob, MediaErasure, Photo
    from apps.safety.crypto import unseal
    from apps.safety.models import ErasureExecution, RightsRequest

    storage = Blob._meta.get_field("original").storage
    absent, live = 0, 0
    for case in RightsRequest.objects.all():
        data = unseal(case.encrypted_payload)
        for name in data["target"]:
            absent += not storage.exists(name)
        for name, expected in zip(data["live"], data["live_hashes"], strict=True):
            if storage.exists(name):
                with storage.open(name, "rb") as source:
                    live += hashlib.sha256(source.read()).hexdigest() == expected
        if cleanup:
            for name in data["target"] + data["live"]:
                assert name.startswith(("originals/media_probe_", "derivatives/media_probe_"))
                storage.delete(name)
    if cleanup:
        from django.conf import settings

        reserved = settings.DATABASES["default"]["NAME"] + "_"
        for folder in ["originals", "derivatives"]:
            try:
                _, files = storage.listdir(folder)
            except FileNotFoundError:
                continue
            for name in files:
                if name.startswith(reserved):
                    storage.delete(folder + "/" + name)
    print(
        json.dumps(
            {
                "completed": MediaErasure.objects.filter(status="completed").count(),
                "target_files_absent": absent,
                "live_files_intact": live,
                "photos": Photo.objects.count(),
                "executions": ErasureExecution.objects.count(),
            }
        ),
        flush=True,
    )


def launch(settings):
    import psycopg
    from psycopg import sql

    database = "media_probe_" + uuid.uuid4().hex[:12]
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
    env = [
        "-e",
        "POSTGRES_DB=" + database,
        "-e",
        "RIGHTS_VERIFICATION_BACKEND=disabled",
        "-e",
        "SAFETY_NOTICE_BACKEND=disabled",
        "-e",
        "CELERY_TASK_ALWAYS_EAGER=0",
    ]
    module = "scripts.probe_media_erasure_worker"
    prefix = ["docker", "exec", worker, "python", "-m", module]

    def wait(count):
        deadline = time.monotonic() + 85
        while time.monotonic() < deadline:
            current = json.loads(command(prefix + ["state"]))
            if current["completed"] == count:
                assert current["target_files_absent"] == current["live_files_intact"] == count * 2
                assert current["photos"] == count * 2 and current["executions"] == count
                return current
            time.sleep(1)
        raise RuntimeError("Physical erasure probe timed out")

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
                "-m",
                module,
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        before = json.loads(command(prefix + ["state"]))
        assert before["target_files_absent"] == 0 and before["live_files_intact"] == 2
        task_id = json.loads(command(prefix + ["dispatch", "--queue", database]))["task_id"]
        first = wait(1)
        print(json.dumps({"worker_passed": True, "task_id": task_id, "state": first}), flush=True)
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
                *env,
                "beat",
                "python",
                "-m",
                module,
                "beat",
                "--queue",
                database,
            ]
        )
        started = time.monotonic()
        final = wait(2)
        beat_log = command(["docker", "logs", beat])
        # Celery writes logs to stderr; capture both streams without exposing payloads.
        log = subprocess.run(["docker", "logs", beat], capture_output=True, text=True, check=True)
        assert "erase-private-media" in beat_log + log.stderr
        log = subprocess.run(["docker", "logs", worker], capture_output=True, text=True, check=True)
        assert "apps.mediafiles.tasks.erase_media_files" in log.stdout + log.stderr
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "state": final,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "isolated_database": database,
                }
            ),
            flush=True,
        )
    finally:
        subprocess.run(["docker", "rm", "-f", beat], capture_output=True)
        cleanup = subprocess.run(prefix + ["cleanup"], capture_output=True, text=True)
        subprocess.run(
            ["docker", "exec", worker, "celery", "-A", "config", "purge", "-Q", database, "-f"],
            capture_output=True,
        )
        subprocess.run(["docker", "rm", "-f", worker], capture_output=True)
        connection.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
        )
        connection.close()
        assert cleanup.returncode == 0, "Inspect isolated probe file cleanup"
        print("Isolated probe database, containers and synthetic files removed", flush=True)


if __name__ == "__main__":
    main()
