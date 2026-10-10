"""Pure digest equivalence plus actual PG physical reads and late rollback."""

import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from uuid import uuid4

import pytest
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety import rights_operation_content_digests as digests

pytestmark = pytest.mark.django_db(transaction=True)


def counted_native(monkeypatch, *, active_only=False):
    original, calls = digests._native_sha256, []

    def counted(content):
        if not active_only or digests._current.get() is not None:
            calls.append(len(content))
        return original(content)

    monkeypatch.setattr(digests, "_native_sha256", counted)
    return calls


def test_exact_bytes_native_equivalence_drift_never_replaces_original(monkeypatch):
    key, calls = (uuid4(), uuid4(), uuid4()), counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for value in [b"original", bytes(bytearray(b"original")), b"originaL", b"originaL", b"original"]:
            assert digests.content_digest(key, value) == hashlib.sha256(value).hexdigest()
        assert len(calls) == 3
        assert digests._current.get()["entries"][key][0] == b"original"
    assert digests._current.get() is None


def test_different_identity_same_bytes_does_not_share_entries(monkeypatch):
    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for key in [(1, 2, 3), (1, 2, 4), (1, 3, 3)]:
            assert digests.content_digest(key, b"same") == hashlib.sha256(b"same").hexdigest()
        assert len(calls) == 3


def test_bounds_repeat_overflow_is_native_and_clear_releases_bytes(monkeypatch):
    monkeypatch.setattr(digests, "MAX_ENTRIES", 1)
    monkeypatch.setattr(digests, "MAX_BYTES", 4)
    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        state = digests._current.get()
        digests.content_digest((1, 2, 3), b"four")
        for _ in range(2):
            digests.content_digest((1, 2, 4), b"small")
            digests.content_digest((1, 2, 5), b"x")
        assert len(calls) == 5
        assert len(state["entries"]) == 1 and state["bytes"] == 4
    assert not state["entries"] and state["bytes"] == 0


def test_nested_failure_thread_pid_connection_and_repeat_isolation(monkeypatch):
    calls, key = counted_native(monkeypatch), (1, 2, 3)
    with transaction.atomic(), digests.operation_content_digests():
        outer = digests._current.get()
        digests.content_digest(key, b"same")
        with pytest.raises(RuntimeError, match="nested"):
            with digests.operation_content_digests():
                digests.content_digest(key, b"same")
                raise RuntimeError("nested")
        assert digests._current.get() is outer
        digests.content_digest(key, b"same")
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(context.run, digests.content_digest, key, b"same").result()
        with monkeypatch.context() as patch:
            patch.setattr(digests.os, "getpid", lambda: -1)
            digests.content_digest(key, b"same")
        with monkeypatch.context() as patch:
            patch.setattr(digests.transaction, "get_connection", lambda: object())
            digests.content_digest(key, b"same")
        assert len(calls) == 5
    with transaction.atomic(), digests.operation_content_digests():
        digests.content_digest(key, b"same")
        assert len(calls) == 6


def test_unsupported_types_errors_and_outside_context_stay_native(monkeypatch):
    class Bytes(bytes):
        pass

    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for key, value in [((1, 2, 3), Bytes(b"x")), ((1, 2, 3), bytearray(b"x")),
                           ((1, 2, object()), b"x"), ((1, 2, "x" * 129), b"x")]:
            assert digests.content_digest(key, value) == hashlib.sha256(value).hexdigest()
        assert not digests._current.get()["entries"]
        with pytest.raises(TypeError):
            digests.content_digest((1, 2, 3), "not bytes")
    assert len(calls) == 5
    assert digests.content_digest((1, 2, 3), b"x") == hashlib.sha256(b"x").hexdigest()
    with pytest.raises(RuntimeError, match="atomic"):
        with digests.operation_content_digests():
            pass


def test_empty_bytes_exact_byte_limit_and_ended_atomic_are_native_when_required(monkeypatch):
    calls = counted_native(monkeypatch)
    monkeypatch.setattr(digests, "MAX_BYTES", 4)
    scope = digests.operation_content_digests()
    try:
        with transaction.atomic():
            scope.__enter__()
            assert digests.content_digest((1, 2, 3), b"") == hashlib.sha256(b"").hexdigest()
            assert digests.content_digest((1, 2, 3), b"") == hashlib.sha256(b"").hexdigest()
            digests.content_digest((1, 2, 4), b"four")
            assert digests._current.get()["bytes"] == 4
        # Same Django connection, but the anchored atomic is gone: no cache hit,
        # even if an unrelated new atomic opens before the scope is reset.
        digests.content_digest((1, 2, 4), b"four")
        with transaction.atomic():
            digests.content_digest((1, 2, 4), b"four")
        assert len(calls) == 4
    finally:
        scope.__exit__(None, None, None)
    assert digests._current.get() is None


def test_bounded_immutable_metadata_exact_types_and_custom_fallback(monkeypatch):
    class Integer(int):
        pass

    class String(str):
        pass

    class Identifier(type(uuid4())):
        pass

    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for key in [(1 << 127, "s" * 128, uuid4()), (1, b"b" * 128, 3)]:
            digests.content_digest(key, b"same")
            digests.content_digest(key, b"same")
        assert len(calls) == 2
        for key in [(True, 2, 3), (Integer(1), 2, 3), (String("x"), 2, 3),
                    (Identifier(str(uuid4())), 2, 3), (1 << 128, 2, 3),
                    ("s" * 129, 2, 3), (b"b" * 129, 2, 3)]:
            digests.content_digest(key, b"same")
            digests.content_digest(key, b"same")
        assert len(calls) == 16 and len(digests._current.get()["entries"]) == 2


@pytest.mark.usefixtures("photo_environment")
def test_finite_real_pg_64mib_retention_arithmetic_not_aggregate_capacity(
    request, settings, monkeypatch
):
    """Finite PG/read/cap proof; NOT 1GiB RSS, 6GiB peak or capacity evidence."""
    from django.core.files.base import ContentFile
    from PIL import Image

    from apps.core.models import Person
    from apps.mediafiles.models import Blob, Photo
    from apps.safety import rights_exports

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    revision = person.listing.revisions.first()
    size, identifiers, expected = 4 * 1024 * 1024, [], {}

    def derivative(index, target_size):
        image = Image.new("RGB", (24, 24), (index + 40, 90, 170))
        # Valid empty little-endian TIFF IFD, padded inside a native WebP EXIF
        # metadata chunk. Pillow's mux writes the actual RIFF size/feature bits.
        exif = b"II*\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        output = io.BytesIO()
        image.save(output, format="WEBP", lossless=True, exif=exif)
        overhead = len(output.getvalue())
        output.close()
        output = io.BytesIO()
        image.save(output, format="WEBP", lossless=True,
                   exif=exif + b"\x00" * (target_size - overhead))
        value = output.getvalue()
        output.close()
        image.close()
        assert len(value) == target_size
        with Image.open(io.BytesIO(value)) as decoded:
            decoded.load()
            assert decoded.size == (24, 24)
            assert decoded.getpixel((0, 0)) == (index + 40, 90, 170)
        return value

    for index in range(17):
        value = derivative(index, size if index < 16 else 1024)
        digest = hashlib.sha256(value).hexdigest()
        blob = Blob.objects.create(sha256=digest, status="ready", width=24, height=24)
        blob.derivative.save(str(uuid4()) + ".webp", ContentFile(value))
        photo = Photo.objects.create(revision=revision, blob=blob, position=200 + index)
        identifiers.append(photo.pk)
        expected[photo.pk] = digest
        del value  # Retain identifiers/digests only, never a fixture payload list.

    native_read, reads = rights_exports._read_image_blob, []

    def physical(blob):
        reads.append(blob.pk)
        return native_read(blob)

    monkeypatch.setattr(rights_exports, "_read_image_blob", physical)
    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for _ in range(4):
            for photo, value in rights_exports.image_contents(person, identifiers[:16]):
                assert len(value) == size
                assert digests.content_digest((person.pk, photo.pk, photo.blob_id), value) == expected[photo.pk]
                del value
        state = digests._current.get()
        assert len(reads) == 64 and len(calls) == 16
        assert state["bytes"] == 64 * 1024 * 1024 and len(state["entries"]) == 16
        first_key = next(iter(state["entries"]))
        retained = state["entries"][first_key]
        for _ in range(2):
            for photo, value in rights_exports.image_contents(person, identifiers[16:]):
                assert digests.content_digest((person.pk, photo.pk, photo.blob_id), value) == expected[photo.pk]
                del value
        assert len(calls) == 18 and len(reads) == 66
        assert len(state["entries"]) == 16 and state["bytes"] == 64 * 1024 * 1024
        assert state["entries"][first_key] is retained
        # Separate byte-only overflow: permit another entry but keep64MiB cap.
        monkeypatch.setattr(digests, "MAX_ENTRIES", 17)
        extra_key = (uuid4(), uuid4(), uuid4())
        for _ in range(2):
            digests.content_digest(extra_key, b"one-extra-byte")
        assert len(calls) == 20 and len(state["entries"]) == 16
        assert state["entries"][first_key] is retained
    assert not state["entries"] and state["bytes"] == 0


@pytest.mark.usefixtures("photo_environment")
def test_real_pg_sixteen_images_four_children_keep_64_physical_reads_16_hashes(
    request, settings, monkeypatch
):
    from test_rights_image_contents_bulk import images

    from apps.safety import rights_exports

    person, rows = images(request, settings, count=16)
    expected = {photo.pk: hashlib.sha256(value).hexdigest() for photo, value in rows}
    original, reads = rights_exports._read_image_blob, []

    def read(blob):
        reads.append(blob.pk)
        return original(blob)

    monkeypatch.setattr(rights_exports, "_read_image_blob", read)
    calls = counted_native(monkeypatch)
    with transaction.atomic(), digests.operation_content_digests():
        for _ in range(4):
            for photo, value in rights_exports.image_contents(person, [row[0].pk for row in rows]):
                assert digests.content_digest((person.pk, photo.pk, photo.blob_id), value) == expected[photo.pk]
                del value
    assert len(reads) == 64 and len(calls) == 16


def test_actual_batch_late_same_size_corruption_rolls_back_with_digest_reuse(request, settings, monkeypatch):
    from test_rights_portability_batch_projection import (
        test_actual_binary_bytes_changed_after_second_child_are_not_cached as original_test,
    )

    calls = counted_native(monkeypatch, active_only=True)
    original_test(request, settings, monkeypatch)
    # First bytes hashed once, second child's exact bytes reuse it, changed
    # third-child bytes are freshly hashed and fail the original declaration.
    assert len(calls) == 2
    assert digests._current.get() is None


def test_actual_four_child_batch_retains_each_physical_audit(request, settings, monkeypatch):
    from test_rights_portability_batch_projection import REASON, prepared

    from apps.safety import rights_exports
    from apps.safety import rights_portability_coverage_batch as batch
    from apps.safety.models import RightsPortabilityCoverageRead, RightsPortabilitySelectionRead

    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    original, reads = rights_exports._read_image_blob, []

    def read(blob):
        reads.append(blob.pk)
        return original(blob)

    monkeypatch.setattr(rights_exports, "_read_image_blob", read)
    calls = counted_native(monkeypatch, active_only=True)
    before = RightsPortabilitySelectionRead.objects.count()
    assert len(batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions")) == 4
    assert len(reads) == 4 and len(calls) == 1
    assert RightsPortabilitySelectionRead.objects.count() == before + 4
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == 4
    assert digests._current.get() is None


def test_actual_audit_removed_after_second_child_rejects_even_for_identical_bytes(
    request, settings, monkeypatch
):
    from django.core.exceptions import ValidationError
    from test_rights_portability_batch_projection import REASON, prepared

    from apps.safety import rights_portability_coverage_batch as batch
    from apps.safety.models import (
        RightsAction,
        RightsImageAccess,
        RightsPortabilityCoverageRead,
        RightsPortabilitySelectionRead,
    )

    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    original, children = batch.inspect_page, []
    before = (RightsAction.objects.count(), RightsImageAccess.objects.filter(request=case).count(),
              RightsPortabilitySelectionRead.objects.count())

    def removed(*args, **kwargs):
        result = original(*args, **kwargs)
        children.append(True)
        if len(children) == 2:
            RightsImageAccess.objects.filter(request=case).delete()
        return result

    monkeypatch.setattr(batch, "inspect_page", removed)
    calls = counted_native(monkeypatch, active_only=True)
    with pytest.raises(ValidationError, match="exact portable image content"):
        batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions")
    assert len(children) == 2 and len(calls) == 1
    assert before == (RightsAction.objects.count(), RightsImageAccess.objects.filter(request=case).count(),
                      RightsPortabilitySelectionRead.objects.count())
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
    assert digests._current.get() is None


@pytest.mark.parametrize("mutation", ["session", "mfa", "permission", "proof", "source", "expiry"])
def test_actual_batch_late_guards_still_rollback(request, settings, monkeypatch, mutation):
    from test_rights_portability_batch_projection import (
        test_late_guard_failure_rolls_back_every_child_with_reused_projection as original_test,
    )

    original_test(request, settings, monkeypatch, mutation)
    assert digests._current.get() is None
