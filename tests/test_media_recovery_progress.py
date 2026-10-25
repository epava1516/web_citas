"""Recovery must progress or stop with an explicit failure, never requeue history forever."""

import hashlib
import json
import time

import pytest
from django.db import connection
from test_media_job_recovery import original_blob
from test_photo_disposition_authority import ledger
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.history import rectification_history_ids
from apps.listings.models import Listing, Revision
from apps.mediafiles import services, tasks
from apps.mediafiles.models import Blob, Photo

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.usefixtures("photo_environment")]


def fixture_revision(settings):
    assert connection.vendor == "postgresql"
    settings.CELERY_TASK_ALWAYS_EAGER = False
    user = User.objects.create(username="synthetic-progress", email="progress@example.invalid")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic progress")
    listing = Listing.objects.create(person=person)
    revision = Revision.objects.create(listing=listing, manager_version=person.manager_version)
    listing.approved_revision = revision
    listing.save(update_fields=["approved_revision"])
    return person, revision


def body_sha(field):
    with field.open("rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def prepared_photo(settings):
    person, revision = fixture_revision(settings)
    item = original_blob("progress")
    photo = Photo.objects.create(revision=revision, blob=item)
    services.process(item.pk)
    item.refresh_from_db()
    photo.refresh_from_db()
    assert item.status == "ready" and item.signature and photo.comparison_complete
    return person, item, photo


def recovery_ticks(item, monkeypatch, count):
    dispatched, rows = [], []
    monkeypatch.setattr(tasks.process_blob, "delay", dispatched.append)
    for tick in range(count):
        dispatched.clear()
        start = time.perf_counter()
        tasks.recover_media_jobs.run()
        select_seconds = time.perf_counter() - start
        assert len(dispatched) == len(set(dispatched)) <= 1
        assert set(dispatched) <= {str(item.pk)}
        failed = False
        process_seconds = None
        if dispatched:
            start = time.perf_counter()
            try:
                services.process(item.pk)
            except OSError:
                failed = True
            process_seconds = time.perf_counter() - start
        item.refresh_from_db()
        rows.append({"tick": tick, "dispatches": len(dispatched), "selector_seconds": select_seconds,
                     "process_seconds": process_seconds, "storage_error": failed,
                     "status": item.status, "attempts": item.attempts,
                     "signature_present": bool(item.signature)})
    return rows


def test_ready_missing_signature_regenerates_and_completes(settings, monkeypatch, record_property):
    _, item, photo = prepared_photo(settings)
    original, derivative = body_sha(item.original), body_sha(item.derivative)
    Blob.objects.filter(pk=item.pk).update(signature={})
    Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    rows = recovery_ticks(item, monkeypatch, 2)
    photo.refresh_from_db()
    record_property("n03d_progress", json.dumps({"kind": "empty_signature", "ticks": rows}))
    assert item.signature and photo.comparison_complete, "Ready without signature never progresses"
    assert item.status == "ready" and item.attempts == 2
    assert [r["dispatches"] for r in rows] == [1, 0]
    assert body_sha(item.original) == original and body_sha(item.derivative) == derivative


def test_ready_history_only_does_not_requeue_or_mark_completed(settings, monkeypatch, record_property):
    person, item, photo = prepared_photo(settings)
    ledger(person)  # Persisted synthetic ledger; no human approval/provider claim.
    assert rectification_history_ids().filter(pk=photo.revision_id).exists()
    Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    original, derivative, signature = body_sha(item.original), body_sha(item.derivative), item.signature
    rows = recovery_ticks(item, monkeypatch, 2)
    photo.refresh_from_db()
    record_property("n03d_progress", json.dumps({"kind": "history_only", "ticks": rows}))
    assert [r["dispatches"] for r in rows] == [0, 0], "Historical-only image requeues without progress"
    assert not photo.comparison_complete
    assert item.status == "ready" and item.attempts == 1 and item.signature == signature
    assert body_sha(item.original) == original and body_sha(item.derivative) == derivative


def test_shared_ready_history_and_current_finishes_current_then_stops(settings, monkeypatch, record_property):
    person, item, history = prepared_photo(settings)
    ledger(person)
    assert rectification_history_ids().filter(pk=history.revision_id).exists()
    revision = Revision.objects.create(listing=person.listing, manager_version=person.manager_version)
    assert not rectification_history_ids().filter(pk=revision.pk).exists()
    current = Photo.objects.create(revision=revision, blob=item)
    Photo.objects.filter(pk=history.pk).update(comparison_complete=False)
    rows = recovery_ticks(item, monkeypatch, 2)
    current.refresh_from_db()
    history.refresh_from_db()
    record_property("n03d_progress", json.dumps({"kind": "mixed_history_current", "ticks": rows}))
    assert current.comparison_complete and not history.comparison_complete
    assert [r["dispatches"] for r in rows] == [1, 0], "Historical sibling keeps completed current work queued"
    assert item.status == "ready" and item.attempts == 1


def test_missing_signature_and_original_is_failed_with_bounded_recovery(settings, monkeypatch, record_property):
    _, item, photo = prepared_photo(settings)
    Blob.objects.filter(pk=item.pk).update(signature={})
    Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    item.original.storage.delete(item.original.name)  # Only this synthetic private fixture file.
    rows = recovery_ticks(item, monkeypatch, 4)
    photo.refresh_from_db()
    record_property("n03d_progress", json.dumps({"kind": "missing_original", "ticks": rows}))
    assert item.status == "failed" and item.attempts == 4, "Missing original silently loops as ready"
    assert item.error_code == "decode_or_storage_failed" and not photo.comparison_complete
    assert [r["dispatches"] for r in rows] == [1, 1, 1, 0]
    assert [r["storage_error"] for r in rows] == [True, True, True, False]
