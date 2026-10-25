"""Finite PostgreSQL recovery selection and real local processing; dispatch captured."""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event, get_ident

import pytest
from django.core.files.base import ContentFile
from django.db import close_old_connections, connection, connections
from django.utils import timezone
from PIL import Image
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.mediafiles import services, tasks
from apps.mediafiles.models import Blob, Photo

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.usefixtures("photo_environment")]


def blob(label, **kwargs):
    return Blob.objects.create(sha256=hashlib.sha256(label.encode()).hexdigest(), **kwargs)


def original_blob(label, **kwargs):
    item = blob(label, **kwargs)
    raw = raw_image(43)
    item.sha256 = hashlib.sha256(raw).hexdigest()
    item.original.save(label + '.jpg', ContentFile(raw))
    return item


@pytest.mark.parametrize('count', [0, 1, 10, 100, 101])
def test_recovery_batch_is_bounded_with_equivalent_selection(count, monkeypatch, record_property):
    assert connection.vendor == 'postgresql'
    items = [blob(f'queued-{n}') for n in range(count)]
    expected = {str(item.pk) for item in items}
    captured, samples = [], []
    monkeypatch.setattr(tasks.process_blob, 'delay', captured.append)
    for ordinal in range(6):
        captured.clear()
        sql_count = 0

        def observe(execute, sql, params, many, context):
            nonlocal sql_count
            sql_count += 1
            return execute(sql, params, many, context)

        started = time.perf_counter()
        with connection.execute_wrapper(observe):
            tasks.recover_media_jobs.run()
        elapsed = time.perf_counter() - started
        assert len(captured) == len(set(captured)) == min(count, 100)
        assert set(captured) <= expected
        if count <= 100:
            assert set(captured) == expected
        assert sql_count == 1
        samples.append({'ordinal': ordinal, 'seconds': elapsed, 'queries': sql_count,
                        'dispatches': len(captured)})
    # No ordering/fairness promise: after the first selected cohort is resolved,
    # the finite overflow must become eligible on the next call.
    first = set(captured)
    Blob.objects.filter(pk__in=first).update(status='ready')
    captured.clear()
    tasks.recover_media_jobs.run()
    assert set(captured) == expected - first
    record_property('n03c_recovery_selection', json.dumps({'count': count, 'samples': samples,
                    'scope': 'Direct real selector with captured dispatch; no broker/Beat/fairness/SLA claim'}))


def test_recovery_selects_states_distinctly_and_excludes_terminal(monkeypatch, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = False
    now = timezone.now()
    expected = [blob('queued'), blob('stale', status='processing', started_at=now-timedelta(seconds=181)),
                blob('failed-0', status='failed'), blob('failed-3', status='failed', attempts=3)]
    excluded = [blob('fresh', status='processing', started_at=now),
                blob('exhausted', status='failed', attempts=4), blob('ready', status='ready')]
    excluded += [blob(status, status=status) for status in ['erasing', 'erased', 'purging', 'purged']]
    user = User.objects.create(username='synthetic-recovery', email='recovery@example.invalid')
    person = Person.objects.create(individual=user, subject=user, alias='Synthetic recovery')
    listing = Listing.objects.create(person=person)
    revision = Revision.objects.create(listing=listing, manager_version=1)
    pending = blob('ready-pending', status='ready')
    Photo.objects.create(revision=revision, blob=pending)
    Photo.objects.create(revision=Revision.objects.create(listing=listing, manager_version=1), blob=pending)
    removed = blob('ready-removed', status='ready')
    Photo.objects.create(revision=revision, blob=removed, removed_at=now)
    complete = blob('ready-complete', status='ready')
    Photo.objects.create(revision=revision, blob=complete, comparison_complete=True)
    expected.append(pending)
    excluded += [removed, complete]
    captured = []
    monkeypatch.setattr(tasks.process_blob, 'delay', captured.append)
    tasks.recover_media_jobs.run()
    assert len(captured) == len(set(captured)) == len(expected)
    assert set(captured) == {str(item.pk) for item in expected}
    assert not set(captured) & {str(item.pk) for item in excluded}


def test_storage_failure_remains_recoverable_and_ready_replay_is_idempotent(monkeypatch):
    item = original_blob('retry')
    storage = item.original.storage
    actual_open = storage.open

    def failing_open(name, *args, **kwargs):
        if name == item.original.name:
            raise OSError('Synthetic original storage outage')
        return actual_open(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(storage, 'open', failing_open)
        with pytest.raises(OSError, match='Synthetic original storage outage'):
            services.process(item.pk)
    item.refresh_from_db()
    assert item.status == 'failed' and item.attempts == 1
    assert item.error_code == 'decode_or_storage_failed' and not item.derivative
    assert storage.exists(item.original.name)
    captured = []
    with monkeypatch.context() as patch:
        patch.setattr(tasks.process_blob, 'delay', captured.append)
        tasks.recover_media_jobs.run()
    assert captured == [str(item.pk)]
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == 'ready' and item.attempts == 2 and item.error_code == ''
    assert item.signature and item.phash and item.regional_hashes
    path = item.derivative.name
    with item.derivative.open('rb') as source:
        image = Image.open(source)
        assert image.format == 'WEBP' and not image.getexif()
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == 'ready' and item.attempts == 2 and item.derivative.name == path


@pytest.mark.parametrize('age,processed', [(1, False), (181, True)])
def test_processing_lease_replays_only_after_expiry(age, processed):
    item = original_blob('lease', status='processing', attempts=1,
                         started_at=timezone.now()-timedelta(seconds=age))
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == ('ready' if processed else 'processing')
    assert item.attempts == (2 if processed else 1)
    assert bool(item.derivative) is processed


@pytest.mark.parametrize('status', ['erasing', 'erased', 'purging', 'purged'])
def test_processing_cannot_resurrect_terminal_media(status, monkeypatch):
    item = blob('terminal-' + status, status=status, attempts=2)

    def forbidden(*args, **kwargs):
        raise AssertionError('Terminal media must never open storage')

    monkeypatch.setattr(item.original.storage, 'open', forbidden)
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == status and item.attempts == 2
    assert not item.derivative and not item.signature


@pytest.mark.parametrize("old_outcome", ["success", "failure"])
def test_expired_worker_cannot_overwrite_new_generation(old_outcome, monkeypatch):
    assert connection.vendor == "postgresql"
    item = original_blob("generation-fence")
    entered, resume = Event(), Event()
    state = {}
    actual_decode = services.decode_image

    def controlled_decode(raw):
        if get_ident() == state.get("old_thread"):
            entered.set()
            assert resume.wait(15), "New generation did not complete before release"
            if old_outcome == "failure":
                raise OSError("Synthetic stale worker failure")
        return actual_decode(raw)

    def old_worker():
        close_old_connections()
        state["old_thread"] = get_ident()
        try:
            services.process(item.pk)
        finally:
            connections.close_all()

    monkeypatch.setattr(services, "decode_image", controlled_decode)
    with ThreadPoolExecutor(max_workers=1) as pool:
        old = pool.submit(old_worker)
        try:
            assert entered.wait(10), "Old generation did not acquire its lease"
            item.refresh_from_db()
            assert item.status == "processing" and item.attempts == 1
            # Simulate passage of the documented lease without a three-minute sleep.
            Blob.objects.filter(pk=item.pk).update(started_at=timezone.now()-timedelta(seconds=181))
            services.process(item.pk)
            item.refresh_from_db()
            assert item.status == "ready" and item.attempts == 2
            new_path, new_started_at = item.derivative.name, item.started_at
        finally:
            resume.set()
        if old_outcome == "failure":
            with pytest.raises(OSError, match="Synthetic stale worker failure"):
                old.result(timeout=15)
        else:
            old.result(timeout=15)
    item.refresh_from_db()
    assert item.status == "ready", "Old failure overwrote the newer successful generation"
    assert item.attempts == 2 and item.started_at == new_started_at
    assert item.derivative.name == new_path, "Old completion replaced the newer derivative"
    assert item.error_code == "" and item.original.storage.exists(new_path)


def test_current_generation_comparison_failure_keeps_existing_retry_state(monkeypatch):
    item = original_blob("own-comparison-error")

    def fail_comparison(blob_id):
        raise OSError("Synthetic current comparison storage failure")

    with monkeypatch.context() as patch:
        patch.setattr(services, "detect_matches", fail_comparison)
        with pytest.raises(OSError, match="Synthetic current comparison storage failure"):
            services.process(item.pk)
    item.refresh_from_db()
    assert item.status == "failed" and item.attempts == 1
    assert item.error_code == "decode_or_storage_failed"
    assert item.original and item.derivative
    assert item.derivative.storage.exists(item.derivative.name)
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == "ready" and item.attempts == 2 and item.error_code == ""
