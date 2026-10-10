"""PostgreSQL durability, authority revocation and broker privacy for async generation."""

import base64
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.urls import reverse
from django.utils import timezone
from redis import Redis
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection
from test_rights_portability_response_draft import operator

from apps.core.models import User
from apps.safety import rights_portability_jobs as jobs
from apps.safety.broker_message_projection import periodic_tasks, project_message
from apps.safety.models import RightsAction, RightsExport, RightsPortabilityExportJob

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic approved private copy generation job"


def prepared(request, settings, monkeypatch, account_only=False):
    case, author, row, decision, person, subject, receipt = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    # Avoid real broker in domain-only tests; the broker test restores dispatch.
    monkeypatch.setattr(jobs, "dispatch", lambda job_id: True)
    return case, author, row, decision, person, subject, receipt


def enqueue(case, author, row, decision, **kwargs):
    return jobs.enqueue(
        author,
        case.pk,
        case.version,
        row.pk,
        decision.pk,
        kwargs.pop("key", uuid4()),
        kwargs.pop("reason", REASON),
        **kwargs,
    )


@pytest.mark.parametrize("account_only", [False, True])
def test_job_durable_replay_and_conflicts(request, settings, monkeypatch, account_only):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch, account_only)
    key = uuid4()
    job = enqueue(case, author, row, decision, key=key)
    assert job.state == "queued" and REASON not in job.encrypted_reason
    assert RightsExport.objects.count() == 0
    assert enqueue(case, author, row, decision, key=key).pk == job.pk
    with pytest.raises(ValidationError):
        enqueue(case, author, row, decision, key=key, reason=REASON + " conflict")
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "succeeded" and job.export_id and job.encrypted_reason == ""
    assert RightsExport.objects.count() == 1
    assert enqueue(case, author, row, decision, key=key).pk == job.pk
    jobs.run(job.pk)
    assert RightsExport.objects.count() == 1
    assert RightsAction.objects.filter(operation="portability_export", key=key).count() == 1


@pytest.mark.parametrize(
    "change", ["session", "mfa", "permission", "assignment", "proof", "source", "expiry"]
)
def test_job_rejects_changed_authority_source_or_proof(request, settings, monkeypatch, change):
    case, author, row, decision, person, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)
    if change in {"session", "mfa"}:
        field = change + "_version"
        User.objects.filter(pk=author.pk).update(**{field: getattr(author, field) + 1})
    elif change == "permission":
        author.user_permissions.clear()
    elif change == "assignment":
        case.assigned_to = None
        case.save(update_fields=["assigned_to"])
    elif change == "proof":
        job.proof.status = "failed"
        job.proof.save(update_fields=["status"])
    elif change == "source":
        person.alias += " changed"
        person.save(update_fields=["alias"])
    else:
        row.expires_at = timezone.now() - timedelta(seconds=1)
        row.save(update_fields=["expires_at"])
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "rejected" and job.encrypted_reason == ""
    assert RightsExport.objects.count() == 0


def test_job_retries_roll_back_partial_generation(request, settings, monkeypatch):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)
    real_generate = jobs.generate

    def crash_after_generate(*args, **kwargs):
        real_generate(*args, **kwargs)
        raise RuntimeError("Synthetic lost commit")

    monkeypatch.setattr(jobs, "generate", crash_after_generate)
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "queued" and job.attempts == 1 and not job.export_id
    assert RightsExport.objects.count() == 0
    case.refresh_from_db()
    assert case.version == job.expected_version
    RightsPortabilityExportJob.objects.filter(pk=job.pk).update(available_at=timezone.now())
    monkeypatch.setattr(jobs, "generate", real_generate)
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "succeeded" and job.attempts == 2


def test_job_lease_recovery(request, settings, monkeypatch):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)
    token = jobs.claim(job.pk)
    assert token is not None and jobs.claim(job.pk) is None
    response = operator(author).get(
        f"/es/moderation/rights/{case.pk}/portability/export/jobs/{job.pk}/"
    )
    assert response.status_code == 200 and "Validando y generando" in response.content.decode()
    RightsPortabilityExportJob.objects.filter(pk=job.pk).update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "succeeded" and job.attempts == 2


def test_expired_job_is_purged_by_reconciler(request, settings, monkeypatch):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)
    RightsPortabilityExportJob.objects.filter(pk=job.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    jobs.reconcile()
    job.refresh_from_db()
    assert job.state == "rejected" and job.encrypted_reason == "" and not job.export_id


def test_two_workers_generate_once(request, settings, monkeypatch):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)

    def execute():
        connections.close_all()
        try:
            jobs.run(job.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute) for _ in range(2)]
        for future in futures:
            future.result(timeout=60)
    job.refresh_from_db()
    assert job.state == "succeeded" and job.attempts == 1
    assert RightsExport.objects.count() == 1


@pytest.mark.parametrize("language", ["es", "en"])
def test_post_queues_and_status_requires_fresh_original_authority(
    request, settings, monkeypatch, language
):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    client = operator(author)
    path = f"/{language}/moderation/rights/{case.pk}/portability/export/"
    response = client.post(
        path, {"key": uuid4(), "version": case.version, "review": decision.pk, "reason": REASON}
    )
    assert response.status_code == 302
    assert RightsExport.objects.count() == 0
    location = response.headers["Location"]
    response = client.get(location)
    assert response.status_code == 200 and "no-store" in response.headers["Cache-Control"]
    assert REASON not in response.content.decode()
    fragment = client.get(location, HTTP_HX_REQUEST="true")
    assert "<html" not in fragment.content.decode() and "hx-get=" in fragment.content.decode()
    jobs.run(RightsPortabilityExportJob.objects.get().pk)
    finished = client.get(location, HTTP_HX_REQUEST="true")
    assert "hx-get=" not in finished.content.decode()
    User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
    assert client.get(location).status_code in {302, 403, 404}


def test_post_without_execute_permission_creates_no_job(request, settings, monkeypatch):
    case, author, _, decision, *_ = prepared(request, settings, monkeypatch)
    author.user_permissions.clear()
    client = operator(User.objects.get(pk=author.pk))
    response = client.post(
        reverse("rights_portability_export", args=[case.pk]),
        {
            "key": uuid4(),
            "version": case.version,
            "review": decision.pk,
            "reason": REASON,
        },
    )
    assert response.status_code == 403
    assert RightsPortabilityExportJob.objects.count() == 0


def test_job_broker_schema_is_typed_and_scoped():
    job_id = str(uuid4())
    wire = {
        "content-type": "application/json",
        "content-encoding": "utf-8",
        "properties": {"body_encoding": "base64"},
        "headers": {"task": "apps.safety.tasks.generate_portability_export"},
        "body": base64.b64encode(json.dumps([[job_id], {}, {}]).encode()).decode(),
    }
    assert wire["headers"]["task"] not in periodic_tasks()
    assert project_message(json.dumps(wire).encode(), set(), "queued", periodic_tasks()) is None
    projected, _ = project_message(
        json.dumps(wire).encode(), set(), "queued", periodic_tasks(), job_ids={job_id}
    )
    assert "generation_reference" in projected and job_id not in json.dumps(projected)
    wire["body"] = base64.b64encode(json.dumps([[{"reason": REASON}], {}, {}]).encode()).decode()
    with pytest.raises(ValueError):
        project_message(
            json.dumps(wire).encode(), set(), "queued", periodic_tasks(), job_ids={job_id}
        )


def test_real_broker_worker_uses_only_job_identifier(request, settings, monkeypatch, tmp_path):
    real_dispatch = jobs.dispatch
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    # The runner provisions an isolated Redis; never point this at normal services.
    settings.CELERY_TASK_ALWAYS_EAGER = False
    job = enqueue(case, author, row, decision)
    monkeypatch.setattr(jobs, "dispatch", real_dispatch)
    from config.celery import app

    queue = "async-test-" + uuid4().hex
    from apps.safety.tasks import generate_portability_export

    generate_portability_export.apply_async(args=[str(job.pk)], queue=queue, ignore_result=True)
    prefix = django_settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    with Redis.from_url(django_settings.CELERY_BROKER_URL) as redis:
        raw = redis.lindex(prefix + queue, 0)
        assert raw is not None and REASON.encode() not in raw
        envelope = json.loads(raw)
        body = json.loads(base64.b64decode(envelope["body"]))
        assert body[0] == [str(job.pk)] and body[1] == {}
    env = os.environ.copy()
    env.update(
        POSTGRES_DB=connection.settings_dict["NAME"],
        RIGHTS_VERIFICATION_BACKEND="simulator",
        SAFETY_ENCRYPTION_KEY=django_settings.SAFETY_ENCRYPTION_KEY,
        DJANGO_SECRET_KEY=django_settings.SECRET_KEY,
    )
    with (tmp_path / "worker.log").open("wb") as log:
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "config",
                "worker",
                "--pool=solo",
                "--concurrency=1",
                "--without-gossip",
                "--without-mingle",
                "--without-heartbeat",
                "-Q",
                queue,
                "--loglevel=WARNING",
            ],
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                job.refresh_from_db()
                if job.state in {"succeeded", "rejected", "failed"}:
                    break
                assert worker.poll() is None
                time.sleep(0.2)
            assert job.state == "succeeded", (job.state, (tmp_path / "worker.log").read_text())
            assert RightsExport.objects.count() == 1
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=5)
            with Redis.from_url(django_settings.CELERY_BROKER_URL) as redis:
                redis.delete(prefix + queue)
            app.close()


def test_broker_outage_preserves_durable_job_and_reconciles(request, settings, monkeypatch):
    real_dispatch = jobs.dispatch
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    monkeypatch.setattr(jobs, "dispatch", real_dispatch)
    from apps.safety.tasks import generate_portability_export

    def outage(**kwargs):
        raise ConnectionError("Synthetic isolated broker unavailable")

    task = generate_portability_export._get_current_object()
    monkeypatch.setattr(task, "apply_async", outage)
    job = enqueue(case, author, row, decision)
    job.refresh_from_db()
    assert job.state == "queued" and job.dispatched_at is None
    assert jobs.reconcile() == 0
    messages = []
    monkeypatch.setattr(task, "apply_async", lambda **kwargs: messages.append(kwargs))
    assert jobs.reconcile() == 1
    assert messages == [{"args": [str(job.pk)], "ignore_result": True}]
    job.refresh_from_db()
    assert job.dispatched_at is not None and job.state == "queued"
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "succeeded"


def test_technical_retries_are_bounded_and_clear_private_reason(
    request, settings, monkeypatch, caplog
):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)

    def outage(*args, **kwargs):
        raise RuntimeError("Synthetic transient generation failure")

    monkeypatch.setattr(jobs, "generate", outage)
    for attempt in range(1, jobs.MAX_ATTEMPTS + 1):
        RightsPortabilityExportJob.objects.filter(pk=job.pk).update(available_at=timezone.now())
        jobs.run(job.pk)
        job.refresh_from_db()
        assert job.attempts == attempt
        assert job.state == ("failed" if attempt == jobs.MAX_ATTEMPTS else "queued")
    assert job.encrypted_reason == "" and job.finished_at is not None
    # Each failed attempt names its exception class, never its private message.
    failures = [r.getMessage() for r in caplog.records if r.name == jobs.__name__]
    assert len(failures) == jobs.MAX_ATTEMPTS
    assert all(m.endswith("attempt failed: RuntimeError") for m in failures)
    assert not any("Synthetic transient" in m for m in failures)
    jobs.run(job.pk)
    assert RightsExport.objects.count() == 0


def test_worker_limits_allow_the_generation_objective_within_the_lease():
    from apps.safety.tasks import generate_portability_export as task

    assert (task.soft_time_limit, task.time_limit) == (jobs.SOFT_TIME_LIMIT, jobs.TIME_LIMIT)
    assert 120 < jobs.SOFT_TIME_LIMIT < jobs.TIME_LIMIT < jobs.LEASE.total_seconds()


@pytest.mark.parametrize("change", ["permission", "proof"])
def test_worker_rechecks_after_observed_postgresql_wait(request, settings, monkeypatch, change):
    from queue import Queue

    from django.db import transaction
    from test_photo_reuse_races import observe_blocked

    from apps.safety.models import RightsRequest

    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    job = enqueue(case, author, row, decision)
    pids = Queue()

    def execute():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            jobs.run(job.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(execute)
            worker = pids.get(timeout=5)
            assert holder != worker
            observe_blocked(worker, holder)
            assert not future.done()
            if change == "permission":
                author.user_permissions.clear()
            else:
                case.proofs.update(status="failed")
        future.result(timeout=60)
    job.refresh_from_db()
    assert job.state == "rejected" and not job.export_id and job.encrypted_reason == ""
    assert RightsExport.objects.count() == 0


@pytest.mark.parametrize("account_only", [False, True])
def test_positive_job_inventory_and_scoped_live_broker(
    request, settings, monkeypatch, account_only
):
    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.rights_access_delivery import broker_records
    from apps.safety.rights_portability_job_inventory import ids
    from apps.safety.tasks import generate_portability_export

    case, author, row, decision, person, subject, *_ = prepared(
        request, settings, monkeypatch, account_only
    )
    settings.CELERY_TASK_ALWAYS_EAGER = False
    job = enqueue(case, author, row, decision)
    assert ids(case) == {str(job.pk)}
    captured = {}

    def capture(label, purpose, query, fields):
        rows = list(query.values(*(fields or [])))
        captured[label] = rows
        return rows

    from django.db import transaction

    with transaction.atomic():
        source_manifest(person, case, capture=capture)
    entries = captured["safety.RightsPortabilityExportJob"]
    assert len(entries) == 1 and entries[0]["pk"] == job.pk
    assert REASON not in str(entries)
    from config.celery import app

    assert app.conf.task_default_queue == django_settings.CELERY_TASK_DEFAULT_QUEUE
    assert app.conf.broker_url == django_settings.CELERY_BROKER_URL
    assert app.conf.broker_transport_options == django_settings.CELERY_BROKER_TRANSPORT_OPTIONS
    assert not app.conf.task_always_eager
    generate_portability_export.apply_async(
        args=[str(job.pk)], ignore_result=True, queue=django_settings.CELERY_TASK_DEFAULT_QUEUE
    )
    prefix = django_settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    with Redis.from_url(django_settings.CELERY_BROKER_URL) as redis:
        queue_key = prefix + django_settings.CELERY_TASK_DEFAULT_QUEUE
        raws = [
            redis.lindex(queue_key + suffix, 0)
            for suffix in ["", "\x06\x163", "\x06\x166", "\x06\x169"]
        ]
        raw = next((value for value in raws if value is not None), None)
        assert raw is not None, (
            "Message must exist in the actual configured private priority queues"
        )
        assert REASON.encode() not in raw
    result = broker_records(set(), case=case)
    assert not result["blocked"] and len(result["copy"]) == 1
    assert "generation_reference" in result["copy"][0]
    assert str(job.pk) not in str(result) and REASON not in str(result)


def test_job_historical_broker_projection_is_explicit_and_pure():
    from test_redis_history_scope import message
    from test_redis_retained_history import command

    from apps.safety.redis_history_scope import scoped_history

    own, foreign = str(uuid4()), str(uuid4())

    def wire(job_id):
        value = json.loads(message(job_id))
        value["headers"]["task"] = "apps.safety.tasks.generate_portability_export"
        return json.dumps(value).encode()

    raw = command(b"LPUSH", b"fixture:q", wire(own), wire(foreign))
    result = scoped_history(
        raw, set(), prefix="fixture:", queue="q", origin_digest="origin", job_ids={own}
    )
    assert not result["blocked"] and len(result["records"]) == 1
    assert "generation_reference" in result["records"][0]["data"]
    assert own not in str(result) and foreign not in str(result)
    no_scope = scoped_history(raw, set(), prefix="fixture:", queue="q", origin_digest="origin")
    assert not no_scope["records"] and not no_scope["blocked"]
