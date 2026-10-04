"""Isolated PostgreSQL/Redis/Celery/Beat probe of JSON and WebP snapshot expiry.

Synthetic task fixtures only: no real rights decision, identity or original media file.
"""

import argparse
import hashlib
import io
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
    assert database.startswith("retention_probe_"), "Isolated database required"
    assert settings.RIGHTS_VERIFICATION_BACKEND == settings.SAFETY_NOTICE_BACKEND == "disabled"
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
        return app.Beat(loglevel="INFO", schedule="/tmp/retention-probe-beat").run()
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
    from PIL import Image

    from apps.core.models import Person, User
    from apps.listings.models import Listing, Revision
    from apps.mediafiles.models import Blob, Photo
    from apps.safety.crypto import cipher, seal
    from apps.safety.models import (
        RightsAction,
        RightsExport,
        RightsExportDownload,
        RightsExportImage,
        RightsExportPart,
        RightsImageAccess,
        RightsProof,
        RightsRequest,
    )
    from apps.safety.rights import fingerprint

    marker = uuid.uuid4().hex
    now = timezone.now()
    payload = io.BytesIO()
    Image.new("RGB", (32, 32), color=(61, 91, 143)).save(payload, format="WEBP")
    content = payload.getvalue()
    with transaction.atomic():
        user = User.objects.create_user(
            username="ops-copy-" + marker, email=marker + "@example.invalid"
        )
        person = Person.objects.create(
            individual=user, subject=user, alias="Synthetic retention task fixture"
        )
        listing = Listing.objects.create(person=person)
        revision = Revision.objects.create(listing=listing, manager_version=1)
        photos = [
            Photo.objects.create(
                revision=revision,
                position=index,
                blob=Blob.objects.create(
                    sha256=fingerprint(marker + str(index)), status="ready", width=32, height=32
                ),
            )
            for index in range(2)
        ]
        case = RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest=fingerprint(marker),
            payload_digest=fingerprint(marker),
            encrypted_payload=seal({"synthetic_task_fixture": True}),
            kind="access",
            person=person,
            manager_version=1,
            reported_individual=user,
            reported_subject=user,
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
            subject_id_snapshot=str(user.pk),
            scope="access",
            channel_digest=case.receipt_digest,
            provider="simulator",
            procedure="rights-simulator-v1",
            payload_digest=fingerprint(marker),
            encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            expires_at=now + timedelta(hours=1),
        )
        # Pending proof and draft source: never eligible for disclosure or publication.
        for photo in photos:
            RightsImageAccess.objects.create(
                request=case,
                actor=user,
                photo=photo,
                case_version=1,
                content_digest=hashlib.sha256(content).hexdigest(),
                purpose="Synthetic task audit fixture, not a real review",
            )
        for expired in [True, False]:
            action = RightsAction.objects.create(
                key=uuid.uuid4(),
                request=case,
                actor=user,
                expected_version=1,
                operation="export",
                payload_digest=fingerprint(marker + str(expired)),
                encrypted_reason=seal({"reason": "Synthetic retention task fixture"}),
            )
            export = RightsExport.objects.create(
                action=action,
                proof=proof,
                person=person,
                case_version=1,
                manager_version=1,
                subject_snapshot=str(user.pk),
                channel_digest=case.receipt_digest,
                encrypted_payload=seal({"synthetic_only": True, "marker": marker}),
                expires_at=now + timedelta(seconds=-1 if expired else 3600),
            )
            for photo in photos:
                image = RightsExportImage.objects.create(
                    export=export, photo=photo, encrypted_content=cipher().encrypt(content).decode()
                )
                RightsExportDownload.objects.create(key=uuid.uuid4(), export=export, image=image)
            from apps.safety.rights_copy_parts import packages

            snapshots = [(image.pk, content) for image in export.images.order_by("pk")]
            package = next(packages(snapshots))
            part = RightsExportPart.objects.create(
                export=export,
                position=1,
                attachments=package["attachments"],
                encrypted_content=cipher().encrypt(package["content"]).decode(),
            )
            RightsExportDownload.objects.create(key=uuid.uuid4(), export=export, part=part)
    print(
        json.dumps(
            {
                "synthetic_exports_created": 2,
                "synthetic_images_created": 4,
                "identity_verified": False,
            }
        ),
        flush=True,
    )


def state(app, task_id):
    from django.utils import timezone

    from apps.listings.models import Revision
    from apps.mediafiles.models import Blob, Photo
    from apps.safety.models import (
        RightsAction,
        RightsExport,
        RightsExportDownload,
        RightsExportImage,
        RightsExportPart,
        RightsImageAccess,
        RightsProof,
    )

    live = RightsExport.objects.filter(expires_at__gt=timezone.now()).order_by("pk")
    expired = RightsExport.objects.filter(expires_at__lte=timezone.now()).order_by("pk")
    live_images = RightsExportImage.objects.filter(export__in=live).order_by("pk")
    expired_images = RightsExportImage.objects.filter(export__in=expired)
    live_parts = RightsExportPart.objects.filter(export__in=live).order_by("pk")
    expired_parts = RightsExportPart.objects.filter(export__in=expired)
    # Ciphertext comparisons establish byte preservation without exposing copy contents.
    preservation = (
        list(live.values_list("pk", "encrypted_payload", "purged_at"))
        + list(live_images.values_list("pk", "encrypted_content"))
        + list(live_parts.values_list("pk", "encrypted_content", "attachments"))
        + list(Blob.objects.order_by("pk").values_list("pk", "sha256", "status", "width", "height"))
    )
    data = {
        "expired": expired.count(),
        "purged": expired.filter(purged_at__isnull=False, encrypted_payload="").count(),
        "expired_images": expired_images.count(),
        "empty_expired_images": expired_images.filter(encrypted_content="").count(),
        "expired_parts": expired_parts.count(),
        "empty_expired_parts": expired_parts.filter(encrypted_content="").count(),
        "live_parts": live_parts.count(),
        "live": live.count(),
        "live_images": live_images.count(),
        "live_content_preserved": not live.filter(encrypted_payload="").exists()
        and not live.filter(purged_at__isnull=False).exists()
        and not live_images.filter(encrypted_content="").exists()
        and not live_parts.filter(encrypted_content="").exists(),
        "preservation_digest": hashlib.sha256(repr(preservation).encode()).hexdigest(),
        "purge_dates": list(expired.values_list("purged_at", flat=True)),
        "actions": RightsAction.objects.count(),
        "proofs": RightsProof.objects.count(),
        "image_accesses": RightsImageAccess.objects.count(),
        "downloads": RightsExportDownload.objects.count(),
        "source_photos": Photo.objects.count(),
        "source_revisions": Revision.objects.count(),
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
    while time.monotonic() < deadline:
        args = ["state"] + (["--task-id", task_id] if task_id else [])
        result = json.loads(command(prefix + args))
        if (
            result["expired"] == result["purged"] == expired
            and result["expired_images"] == result["empty_expired_images"] == expired * 2
            and result["expired_parts"] == result["empty_expired_parts"] == expired
            and (not task_id or result["task"]["status"] == "SUCCESS")
        ):
            assert (
                result["live"] == expired
                and result["live_images"] == expired * 2
                and result["live_parts"] == expired
                and result["live_content_preserved"]
            )
            assert result["actions"] == expired * 2 and result["proofs"] == expired
            assert result["image_accesses"] == result["source_photos"] == expired * 2
            assert result["downloads"] == expired * 6 and result["source_revisions"] == expired
            return result
        time.sleep(1)
    print(json.dumps({"probe_timeout_state": result}), flush=True)
    raise AssertionError("Retention worker or Beat did not reach expected state")


def launch(settings):
    import psycopg
    from psycopg import sql

    config = json.loads(command(["docker", "compose", "config", "--format", "json"]))
    assert config["services"]["worker"]["environment"].get("APP_ENV", "development") != "production"
    database = "retention_probe_" + uuid.uuid4().hex[:12]
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
    ]
    prefix = ["docker", "exec", worker, "python", "-m", "scripts.probe_export_retention_worker"]
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
                "scripts.probe_export_retention_worker",
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
                    "expired_image_contents_removed": 2,
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
                "scripts.probe_export_retention_worker",
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
                r"Task apps\.safety\.tasks\.purge_expired_exports\[([a-f0-9-]+)\] received", text
            )
        )
        succeeded = set(
            re.findall(
                r"Task apps\.safety\.tasks\.purge_expired_exports\[([a-f0-9-]+)\] succeeded", text
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
                    "expired_image_contents_removed": 4,
                    "live_image_contents_preserved": 4,
                    "audit_preserved": True,
                    "original_media_files_verified": False,
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
