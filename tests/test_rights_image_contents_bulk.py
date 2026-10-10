"""Finite real PostgreSQL bulk-lock regressions; run only in a coordinated window."""

import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import connection, connections, transaction
from django.http import Http404
from django.test.utils import CaptureQueriesContext
from PIL import Image
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.mediafiles.models import Blob, Photo
from apps.safety import rights_exports
from apps.safety.rights_exports import image_content, image_contents

pytestmark = pytest.mark.django_db(transaction=True)


def images(request, settings, count=3):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    revision = person.listing.revisions.first()
    rows = []
    for index in range(count):
        output = io.BytesIO()
        Image.new("RGB", (24, 24), (index + 40, 90, 170)).save(output, format="WEBP", lossless=True)
        content = output.getvalue()
        blob = Blob.objects.create(sha256=hashlib.sha256(content).hexdigest(), status="ready")
        blob.derivative.save(str(uuid4()) + ".webp", ContentFile(content))
        photo = Photo.objects.create(revision=revision, blob=blob, position=100 + index)
        rows.append((photo, content))
    return person, rows


@pytest.mark.usefixtures("photo_environment")
def test_sixteen_images_four_calls_keep_sixty_four_physical_reads(request, settings, monkeypatch):
    person, rows = images(request, settings, count=16)
    original = rights_exports._read_image_blob
    reads = []
    expected = {photo.pk: hashlib.sha256(content).hexdigest() for photo, content in rows}

    def counted(blob):
        reads.append(blob.pk)
        return original(blob)

    monkeypatch.setattr(rights_exports, "_read_image_blob", counted)
    with transaction.atomic(), CaptureQueriesContext(connection) as queries:
        for _ in range(4):
            for photo, content in image_contents(person, [row[0].pk for row in rows]):
                assert hashlib.sha256(content).hexdigest() == expected[photo.pk]
                del content
    assert len(reads) == 64 and len(queries) == 12


@pytest.mark.usefixtures("photo_environment")
def test_bulk_fresh_metadata_is_three_queries_and_preserves_single_bytes(request, settings):
    person, rows = images(request, settings)
    ordered = list(reversed(rows))
    with transaction.atomic(), CaptureQueriesContext(connection) as queries:
        actual = list(image_contents(person, [photo.pk for photo, _ in ordered]))
    assert len(queries) == 3
    assert [(photo.pk, content) for photo, content in actual] == [(photo.pk, content) for photo, content in ordered]
    with transaction.atomic():
        for photo, content in ordered:
            assert image_content(person, photo.pk)[1] == content
    # Metadata must be fetched again, even inside the same enclosing transaction.
    with transaction.atomic():
        list(image_contents(person, [rows[0][0].pk]))
        Blob.objects.filter(pk=rows[0][0].blob_id).update(status="erasing")
        with pytest.raises(ValidationError):
            list(image_contents(person, [rows[0][0].pk]))
    foreign = Person.objects.get(subject__username="fixture-v1-model-b")
    with transaction.atomic(), pytest.raises(Http404):
        list(image_contents(foreign, [rows[0][0].pk]))
    with transaction.atomic(), CaptureQueriesContext(connection) as queries:
        assert list(image_contents(person, [])) == []
    assert len(queries) == 0
    with transaction.atomic(), pytest.raises(ValidationError, match="Duplicate"):
        list(image_contents(person, [rows[0][0].pk, rows[0][0].pk]))


@pytest.mark.usefixtures("photo_environment")
def test_bulk_rejects_mapping_changed_during_actual_blob_lock_wait(request, settings):
    person, rows = images(request, settings)
    target, _ = rows[0]
    replacement = rows[1][0].blob_id
    # Avoid the same-revision active-photo uniqueness constraint on replacement.
    Photo.objects.filter(pk=rows[1][0].pk).delete()
    pids = Queue()

    def reader():
        connections.close_all()
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout='8s'")
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
                with pytest.raises(ValidationError, match="changed while waiting"):
                    list(image_contents(person, [target.pk]))
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(), connection.cursor() as cursor:
            Blob.objects.select_for_update().get(pk=target.blob_id)
            cursor.execute("SELECT pg_backend_pid()")
            holder = cursor.fetchone()[0]
            future = pool.submit(reader)
            observe_blocked(pids.get(timeout=5), holder)
            Photo.objects.filter(pk=target.pk).update(blob_id=replacement)
        future.result(timeout=10)


@pytest.mark.usefixtures("photo_environment")
def test_reverse_bulk_and_single_readers_complete_with_real_pg_locks(request, settings):
    person, rows = images(request, settings)
    barrier = Barrier(3)

    def reader(reverse=False, single=False):
        connections.close_all()
        try:
            ordered = rows[::-1] if reverse else rows
            barrier.wait(timeout=5)
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout='8s'")
                cursor.execute("SET LOCAL statement_timeout='10s'")
                if single:
                    photo, content = image_content(person, ordered[0][0].pk)
                    return [(photo.pk, hashlib.sha256(content).hexdigest())]
                return [(photo.pk, hashlib.sha256(content).hexdigest())
                        for photo, content in image_contents(person, [item[0].pk for item in ordered])]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=3) as pool:
        forward = pool.submit(reader)
        backward = pool.submit(reader, True)
        single = pool.submit(reader, True, True)
        expected = [(photo.pk, hashlib.sha256(content).hexdigest()) for photo, content in rows]
        assert forward.result(timeout=15) == expected
        assert backward.result(timeout=15) == expected[::-1]
        assert single.result(timeout=15) == expected[-1:]


@pytest.mark.usefixtures("photo_environment")
def test_physical_bytes_changed_between_children_roll_back_all_batch_audits(
    request, settings, monkeypatch
):
    from test_rights_portability_batch_projection import prepared

    from apps.safety import rights_portability_coverage_batch as batch
    from apps.safety.crypto import unseal
    from apps.safety.models import (
        RightsAction,
        RightsPortabilityCoverageRead,
        RightsPortabilitySelectionRead,
    )

    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    declaration = unseal(coverage.selection_review.selection.encrypted_selection)["images"][0]
    derivative = Photo.objects.get(pk=declaration["photo"]).blob.derivative
    with derivative.open("rb") as stream:
        original_bytes = stream.read()
    changed = bytearray(original_bytes)
    changed[-1] ^= 1
    original_page, original_read = batch.inspect_page, rights_exports._read_image_blob
    children, physical_reads = [], []
    counts = (RightsAction.objects.count(), RightsPortabilitySelectionRead.objects.count())

    def read(blob):
        physical_reads.append(blob.pk)
        return original_read(blob)

    def page(*args, **kwargs):
        result = original_page(*args, **kwargs)
        children.append(True)
        if len(children) == 2:
            with derivative.open("wb") as stream:
                stream.write(changed)
        return result

    monkeypatch.setattr(rights_exports, "_read_image_blob", read)
    monkeypatch.setattr(batch, "inspect_page", page)
    try:
        with pytest.raises(ValidationError, match="Inspect exact portable image content first"):
            batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(),
                                "Inspect every original page before finite physical drift", "revisions")
        assert len(children) == 2 and len(physical_reads) == 3
        assert (RightsAction.objects.count(), RightsPortabilitySelectionRead.objects.count()) == counts
        assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
    finally:
        with derivative.open("wb") as stream:
            stream.write(original_bytes)
