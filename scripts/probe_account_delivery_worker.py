"""Isolated PostgreSQL/Redis/Celery/Beat probe of account delivery expiry.

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
    assert database.startswith("account_delivery_probe_"), "Isolated database required"
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
            "purge-expired-account-confirmation-delivery": settings.CELERY_BEAT_SCHEDULE[
                "purge-expired-account-confirmation-delivery"
            ]
        }
        return app.Beat(loglevel="INFO", schedule="/tmp/account-delivery-probe-beat").run()
    if options.mode == "fixture":
        fixture()
    elif options.mode == "dispatch":
        from apps.safety.tasks import purge_expired_account_confirmation_delivery

        job = purge_expired_account_confirmation_delivery.apply_async(
            queue=options.queue, ignore_result=False
        )
        print(json.dumps({"task_id": job.id}), flush=True)
    else:
        state(app, options.task_id)


def fixture():
    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import Person, User
    from apps.safety.crypto import seal
    from apps.safety.models import (
        RightsAccountEmailConfirmation,
        RightsAction,
        RightsProof,
        RightsRectificationProposal,
        RightsRequest,
    )
    from apps.safety.rights import fingerprint

    marker, now = uuid.uuid4().hex, timezone.now()
    with transaction.atomic():
        user = User.objects.create_user(
            username="ops-delivery-" + marker, email=marker + "@example.invalid"
        )
        person = Person.objects.create(
            individual=user, subject=user, alias="Synthetic delivery task fixture"
        )
        case = RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest=fingerprint(marker),
            payload_digest=fingerprint(marker),
            encrypted_payload=seal({"synthetic_task_fixture": True}),
            kind="rectify",
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
            person_rights_version=person.rights_version,
            subject_id_snapshot=str(user.pk),
            scope="rectify",
            channel_digest=case.receipt_digest,
            provider="simulator",
            procedure="rights-simulator-v1",
            payload_digest=fingerprint(marker),
            encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            expires_at=now + timedelta(hours=1),
        )

        def action(operation):
            return RightsAction.objects.create(
                key=uuid.uuid4(),
                request=case,
                actor=user,
                expected_version=1,
                operation=operation,
                payload_digest=fingerprint(marker),
                encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            )

        proposal = RightsRectificationProposal.objects.create(
            action=action("rectify_plan"),
            proof=proof,
            person=person,
            source_digest=fingerprint(marker),
            encrypted_changes=seal({"synthetic_task_fixture": True}),
        )
        # Pending proof and no approval: these records cannot authorize any account change.
        for expired in (True, False):
            identifier = uuid.uuid4().hex
            RightsAccountEmailConfirmation.objects.create(
                action=action("account_email"),
                proposal=proposal,
                proof=proof,
                subject=user,
                digest=hashlib.sha256(identifier.encode()).hexdigest(),
                source_digest=fingerprint(marker),
                destination_digest=fingerprint(identifier),
                encrypted_delivery=seal(
                    {
                        "synthetic_task_fixture": True,
                        "url": "http://example.invalid/synthetic-link/" + identifier,
                    }
                ),
                expires_at=now + timedelta(seconds=-1 if expired else 86400),
            )
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
        RightsAccountEmailConfirmation,
        RightsAction,
        RightsProof,
        RightsRectificationProposal,
        RightsRequest,
    )

    expired = RightsAccountEmailConfirmation.objects.filter(
        expires_at__lte=timezone.now()
    ).order_by("pk")
    live = RightsAccountEmailConfirmation.objects.filter(expires_at__gt=timezone.now()).order_by(
        "pk"
    )
    metadata = [
        field.attname
        for field in RightsAccountEmailConfirmation._meta.concrete_fields
        if field.name != "encrypted_delivery"
    ]
    preserved = [
        list(model.objects.order_by("pk").values())
        for model in (
            User,
            Person,
            RightsAction,
            RightsProof,
            RightsRequest,
            RightsRectificationProposal,
        )
    ]
    preserved.append(list(RightsAccountEmailConfirmation.objects.order_by("pk").values(*metadata)))
    preserved.append(list(live.values("pk", "encrypted_delivery")))
    data = {
        "expired": expired.count(),
        "purged": expired.filter(encrypted_delivery="").count(),
        "live": live.count(),
        "live_content_preserved": not live.filter(encrypted_delivery="").exists(),
        "preservation_digest": hashlib.sha256(
            json.dumps(preserved, sort_keys=True, default=str).encode()
        ).hexdigest(),
        "purge_dates": list(
            expired.values_list("pk", "created_at", "confirmed_at", "consumed_at", "revoked_at")
        ),
        "actions": RightsAction.objects.count(),
        "proofs": RightsProof.objects.count(),
        "proposals": RightsRectificationProposal.objects.count(),
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
            assert (
                result["users"]
                == result["people"]
                == result["proofs"]
                == result["proposals"]
                == expired
            )
            assert result["actions"] == expired * 3
            return result
        time.sleep(1)
    print(json.dumps({"probe_timeout_state": result}), flush=True)
    raise AssertionError("Account delivery worker or Beat did not reach expected state")


def launch(settings):
    import psycopg
    from psycopg import sql

    config = json.loads(command(["docker", "compose", "config", "--format", "json"]))
    assert config["services"]["worker"]["environment"].get("APP_ENV", "development") != "production"
    database = "account_delivery_probe_" + uuid.uuid4().hex[:12]
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
    prefix = ["docker", "exec", worker, "python", "-m", "scripts.probe_account_delivery_worker"]
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
                "scripts.probe_account_delivery_worker",
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
                    "expired_delivery_payloads_removed": 1,
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
                "scripts.probe_account_delivery_worker",
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
        assert "purge-expired-account-confirmation-delivery" in beat_log.stdout + beat_log.stderr
        worker_log = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        text = worker_log.stdout + worker_log.stderr
        received = set(
            re.findall(
                r"Task apps\.safety\.tasks\.purge_expired_account_confirmation_delivery\[([a-f0-9-]+)\] received",
                text,
            )
        )
        succeeded = set(
            re.findall(
                r"Task apps\.safety\.tasks\.purge_expired_account_confirmation_delivery\[([a-f0-9-]+)\] succeeded",
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
                    "expired_delivery_payloads_removed": 2,
                    "live_delivery_payloads_preserved": 2,
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
