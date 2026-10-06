"""Isolated real PostgreSQL/Redis/Celery/Beat retention probe; synthetic evidence only."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from datetime import timedelta
from pathlib import Path

TASKS = {
    "assessments": "apps.safety.tasks.purge_expired_portability_assessments",
    "selections": "apps.safety.tasks.purge_expired_portability_selections",
    "coverage": "apps.safety.tasks.purge_expired_portability_coverage",
    "response_drafts": "apps.safety.tasks.purge_expired_portability_response_drafts",
}


def command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        print(result.stderr, flush=True)
        result.check_returncode()
    return result.stdout.strip()


def fixture():
    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import User
    from apps.safety import models
    from apps.safety.crypto import seal
    from apps.safety.rights import fingerprint

    now, marker = timezone.now(), uuid.uuid4().hex
    with transaction.atomic():
        actor = User.objects.create_user(
            username="probe-" + marker, email=marker + "@example.invalid"
        )
        case = models.RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            kind="portability",
            account_subject=actor,
            received_at=now,
            initial_due_at=now + timedelta(days=1),
            receipt_expires_at=now + timedelta(days=1),
        )
        digest = fingerprint(marker)
        proof = models.RightsProof.objects.create(
            key=uuid.uuid4(),
            request=case,
            account_subject=actor,
            initiated_by=actor,
            case_version=1,
            subject_id_snapshot=str(actor.pk),
            scope="portability",
            account_source_digest=digest,
            channel_digest=digest,
            provider="simulator",
            procedure="rights-simulator-v1",
            payload_digest=digest,
            encrypted_reason=seal({"synthetic_task_fixture": True}),
            expires_at=now + timedelta(days=1),
        )

        def action(operation):
            return models.RightsAction.objects.create(
                key=uuid.uuid4(),
                request=case,
                actor=actor,
                expected_version=1,
                operation=operation,
                payload_digest=digest,
                encrypted_reason=seal({"synthetic_task_fixture": True}),
            )

        for version, expired in enumerate([True, False], 1):
            expiry = now + timedelta(seconds=-1 if expired else 86400)
            assessment = models.RightsPortabilityAssessment.objects.create(
                request=case,
                actor=actor,
                action=action("portability_save"),
                proof=proof,
                source_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                version=version,
                encrypted_assessment=seal({"synthetic_task_fixture": marker}),
                expires_at=expiry,
            )
            read = models.RightsPortabilityRead.objects.create(
                action=action("portability_inspect"),
                assessment=assessment,
                proof=proof,
                source_digest=digest,
                assessment_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
            )
            review = models.RightsPortabilityReview.objects.create(
                action=action("portability_review"),
                assessment=assessment,
                read=read,
                proof=proof,
                source_digest=digest,
                assessment_digest=digest,
                outcome="rejected",
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
            )
            selection = models.RightsPortabilitySelection.objects.create(
                request=case,
                actor=actor,
                action=action("selection_save"),
                assessment_review=review,
                proof=proof,
                source_digest=digest,
                assessment_digest=digest,
                inspection_digest=digest,
                decision_digest=digest,
                selection_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                version=version,
                encrypted_selection=seal({"synthetic_task_fixture": marker}),
                expires_at=expiry,
            )
            selection_read = models.RightsPortabilitySelectionRead.objects.create(
                action=action("selection_inspect"),
                selection=selection,
                proof=proof,
                source_digest=digest,
                selection_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
            )
            selection_review = models.RightsPortabilitySelectionReview.objects.create(
                action=action("selection_review"),
                selection=selection,
                read=selection_read,
                proof=proof,
                source_digest=digest,
                selection_digest=digest,
                outcome="rejected",
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
            )
            coverage = models.RightsPortabilityCoverage.objects.create(
                request=case,
                actor=actor,
                action=action("coverage_save"),
                selection_review=selection_review,
                proof=proof,
                source_digest=digest,
                selection_digest=digest,
                coverage_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                version=version,
                encrypted_coverage=seal({"synthetic_task_fixture": marker}),
                expires_at=expiry,
            )
            coverage_review = models.RightsPortabilityCoverageReview.objects.create(
                action=action("coverage_review"),
                coverage=coverage,
                proof=proof,
                source_digest=digest,
                coverage_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                outcome="rejected",
            )
            export = models.RightsExport.objects.create(
                action=action("portability_export"),
                proof=proof,
                account_subject=actor,
                case_version=1,
                subject_snapshot=str(actor.pk),
                channel_digest=digest,
                encrypted_payload=seal({"synthetic_task_fixture": marker}),
                expires_at=expiry,
            )
            draft = models.RightsPortabilityResponseDraft.objects.create(
                action=action("portability_draft"),
                request=case,
                actor=actor,
                export=export,
                coverage_review=coverage_review,
                proof=proof,
                case_version=1,
                response_version=0,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                export_digest=digest,
                coverage_digest=digest,
                text_digest=digest,
                encrypted_response=seal({"synthetic_task_fixture": marker}),
                expires_at=expiry,
            )
            models.RightsPortabilityResponseReview.objects.create(
                action=action("final_draft_review"),
                draft=draft,
                read_action=action("final_draft_read"),
                text_digest=digest,
                ciphertext_digest=digest,
                original_session_version=actor.session_version,
                original_mfa_version=actor.mfa_version,
                outcome="rejected",
            )
    print(json.dumps({"fixture_created": True, "identity_approved": False}), flush=True)


def state(app, jobs):
    from django.utils import timezone

    from apps.core.models import User
    from apps.safety import models

    preserved, data = [], {}
    for label, name, body in [
        ("assessments", "RightsPortabilityAssessment", "encrypted_assessment"),
        ("selections", "RightsPortabilitySelection", "encrypted_selection"),
        ("coverage", "RightsPortabilityCoverage", "encrypted_coverage"),
        ("response_drafts", "RightsPortabilityResponseDraft", "encrypted_response"),
    ]:
        model = getattr(models, name)
        fields = [
            f.attname for f in model._meta.concrete_fields if f.name not in {body, "purged_at"}
        ]
        preserved.append(list(model.objects.order_by("pk").values(*fields)))
        expired = model.objects.filter(expires_at__lte=timezone.now())
        live = model.objects.filter(expires_at__gt=timezone.now())
        preserved.append(list(live.order_by("pk").values("pk", body, "purged_at")))
        data[label] = {
            "expired": expired.count(),
            "purged": expired.filter(**{body: "", "purged_at__isnull": False}).count(),
            "live": live.count(),
            "live_preserved": not live.filter(**{body: ""}).exists()
            and not live.filter(purged_at__isnull=False).exists(),
            "purge_dates": list(expired.order_by("pk").values_list("pk", "purged_at")),
        }
    for model in [
        User,
        models.RightsRequest,
        models.RightsProof,
        models.RightsAction,
        models.RightsPortabilityRead,
        models.RightsPortabilityReview,
        models.RightsPortabilitySelectionRead,
        models.RightsPortabilitySelectionReview,
        models.RightsPortabilityCoverageReview,
        models.RightsExport,
        models.RightsPortabilityResponseReview,
    ]:
        preserved.append(list(model.objects.order_by("pk").values()))
    data["preservation_digest"] = hashlib.sha256(
        json.dumps(preserved, sort_keys=True, default=str).encode()
    ).hexdigest()
    data["jobs"] = {
        label: {
            "status": app.AsyncResult(job).status,
            "result": app.AsyncResult(job).result if app.AsyncResult(job).successful() else None,
        }
        for label, job in jobs.items()
    }
    print(json.dumps(data, default=str), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["launch", "worker", "beat", "fixture", "state", "dispatch"]
    )
    parser.add_argument("--queue", default="")
    parser.add_argument("--jobs", default="{}")
    args = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    assert not settings.PRODUCTION
    if args.mode == "launch":
        return launch(settings)
    database = settings.DATABASES["default"]["NAME"]
    assert database.startswith("portability_probe_")
    assert settings.RIGHTS_VERIFICATION_BACKEND == settings.SAFETY_NOTICE_BACKEND == "disabled"
    from config.celery import app

    app.conf.result_backend = settings.CELERY_BROKER_URL
    app.conf.task_ignore_result = False
    assert not app.conf.task_always_eager
    if args.mode == "worker":
        assert args.queue == database
        return app.worker_main(["worker", "--loglevel=INFO", "--concurrency=1", "-Q", database])
    if args.mode == "beat":
        assert args.queue == database
        app.conf.task_default_queue = database
        selected_schedule = {
            name: settings.CELERY_BEAT_SCHEDULE[name]
            for name in [
                "purge-expired-portability-assessments",
                "purge-expired-portability-selections",
                "purge-expired-portability-coverage",
                "purge-expired-portability-response-drafts",
            ]
        }
        # The Django CELERY namespace takes precedence over lower-case updates.
        app.conf.update(CELERY_BEAT_SCHEDULE=selected_schedule)
        assert app.conf.beat_schedule == selected_schedule
        assert {entry["task"] for entry in app.conf.beat_schedule.values()} == set(TASKS.values())
        return app.Beat(loglevel="INFO", schedule="/tmp/portability-probe-beat").run()
    if args.mode == "fixture":
        return fixture()
    if args.mode == "dispatch":
        assert args.queue == database
        print(
            json.dumps(
                {
                    label: app.send_task(task, queue=database, ignore_result=False).id
                    for label, task in TASKS.items()
                }
            ),
            flush=True,
        )
    else:
        state(app, json.loads(args.jobs))


def launch(settings):
    import psycopg
    from psycopg import sql

    database = "portability_probe_" + uuid.uuid4().hex[:12]
    worker, beat = database + "_worker", database + "_beat"
    db = settings.DATABASES["default"]
    conn = psycopg.connect(
        dbname="postgres",
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        autocommit=True,
    )
    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    env = [
        "-e",
        "POSTGRES_DB=" + database,
        "-e",
        "RIGHTS_VERIFICATION_BACKEND=disabled",
        "-e",
        "SAFETY_NOTICE_BACKEND=disabled",
        "-e",
        "ACCOUNT_CORRECTION_DELIVERY_BACKEND=disabled",
        "-e",
        "CELERY_TASK_ALWAYS_EAGER=0",
        "-v",
        str(Path(__file__).resolve()) + ":/app/probe_portability.py:ro",
    ]
    prefix = ["docker", "exec", worker, "python", "/app/probe_portability.py"]

    def wait(count, jobs=None, timeout=45):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            data = json.loads(command(prefix + ["state", "--jobs", json.dumps(jobs or {})]))
            if all(
                data[label]["expired"] == data[label]["purged"] == count for label in TASKS
            ) and all(row["status"] == "SUCCESS" for row in data["jobs"].values()):
                assert all(
                    data[label]["live"] == count and data[label]["live_preserved"]
                    for label in TASKS
                )
                return data
            time.sleep(1)
        raise AssertionError("Portability retention probe timeout")

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
                "/app/probe_portability.py",
                "worker",
                "--queue",
                database,
            ]
        )
        command(["docker", "exec", worker, "python", "manage.py", "migrate", "--noinput"])
        command(prefix + ["fixture"])
        before = json.loads(command(prefix + ["state"]))
        jobs = json.loads(command(prefix + ["dispatch", "--queue", database]))
        first = wait(1, jobs)
        assert first["preservation_digest"] == before["preservation_digest"]
        assert all(row["result"] == 1 for row in first["jobs"].values())
        repeat = json.loads(command(prefix + ["dispatch", "--queue", database]))
        second = wait(1, repeat)
        assert second["preservation_digest"] == first["preservation_digest"]
        assert all(row["result"] == 0 for row in second["jobs"].values())
        assert all(second[label]["purge_dates"] == first[label]["purge_dates"] for label in TASKS)
        print(
            json.dumps(
                {
                    "worker_passed": True,
                    "jobs": jobs,
                    "repeat": repeat,
                    "audit_and_live_content_preserved": True,
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
                *env,
                "beat",
                "python",
                "/app/probe_portability.py",
                "beat",
                "--queue",
                database,
            ]
        )
        final = wait(2, timeout=90)
        assert final["preservation_digest"] == before_beat["preservation_digest"]
        logs = subprocess.run(
            ["docker", "logs", worker], capture_output=True, text=True, check=True
        )
        text = logs.stdout + logs.stderr
        automatic = {}
        for label, task in TASKS.items():
            received = set(
                re.findall(r"Task " + re.escape(task) + r"\[([a-f0-9-]+)\] received", text)
            )
            succeeded = set(
                re.findall(r"Task " + re.escape(task) + r"\[([a-f0-9-]+)\] succeeded", text)
            )
            automatic[label] = sorted(succeeded - {jobs[label], repeat[label]})
            assert automatic[label] and set(automatic[label]) <= received
        print(
            json.dumps(
                {
                    "beat_passed": True,
                    "automatic_jobs": automatic,
                    "manual_dispatch_for_beat": False,
                    "preservation_digest": final["preservation_digest"],
                    "isolated_database": database,
                    "identity_verified": False,
                }
            ),
            flush=True,
        )
    except Exception:
        logs = subprocess.run(["docker", "logs", worker], capture_output=True, text=True)
        print(logs.stdout + logs.stderr, flush=True)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", beat], capture_output=True)
        subprocess.run(
            ["docker", "exec", worker, "celery", "-A", "config", "purge", "-Q", database, "-f"],
            capture_output=True,
        )
        subprocess.run(["docker", "rm", "-f", worker], capture_output=True)
        conn.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
        conn.close()
        print(json.dumps({"isolated_database_and_containers_removed": True}), flush=True)


if __name__ == "__main__":
    main()
