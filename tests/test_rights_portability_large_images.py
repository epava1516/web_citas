"""Real sanitized synthetic WebP delivery across the actual64MiB package boundary."""

import hashlib
import io
import random
import time
import tracemalloc
import zipfile
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.core.files.base import ContentFile
from django.db import transaction
from django.test import Client
from PIL import Image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url

from apps.mediafiles.models import Blob, Photo
from apps.safety.crypto import unseal
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_image_read import inspect
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)


def test_portable_large_images_cross_actual_package_limit(
    request, settings, monkeypatch, record_property
):
    original_ready = fixtures.ready
    expected = {}

    def ready_with_images(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        revision = result[-1].listing.revisions.first()
        for index in range(8):
            bitmap = Image.frombytes(
                "RGB", (2048, 1536), random.Random(index).randbytes(2048 * 1536 * 3)
            )
            output = io.BytesIO()
            bitmap.save(output, format="WEBP", lossless=True, method=0)
            content = output.getvalue()
            assert len(content) <= 10 * 1024 * 1024
            digest = hashlib.sha256(content).hexdigest()
            blob = Blob.objects.create(sha256=digest, status="ready", width=2048, height=1536)
            blob.derivative.save(f"synthetic-portable-large-{index}.webp", ContentFile(content))
            photo = Photo.objects.create(revision=revision, blob=blob, position=index + 10)
            expected[str(photo.pk)] = (digest, len(content))
        return result

    monkeypatch.setattr(fixtures, "ready", ready_with_images)
    case, author, baseline, previous, person, _, receipt = fixtures.prepared_selection(
        request, settings, monkeypatch, False
    )
    assert sum(size for _, size in expected.values()) > 64 * 1024 * 1024
    reason = "Explicitly inspect synthetic large binary images before portable delivery"
    facts = {
        "status": "eligible",
        "basis": "contract",
        "origin": "provided",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": reason,
        "evidence": "Synthetic retained sanitized binary provenance",
    }
    client = Client()
    client.force_login(author)
    session = client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    decisions = []
    for revision_index, revision in enumerate(source["revisions"]):
        for image_index, image in enumerate(revision["images"]):
            photo_id = image["photo"]
            if photo_id not in expected:
                continue
            response = client.post(
                f"/en/moderation/rights/{case.pk}/image/{photo_id}/", {"purpose": reason}
            )
            assert response.status_code == 200
            assert hashlib.sha256(response.content).hexdigest() == expected[photo_id][0]
            decisions.append(
                {
                    "row": row_reference("revisions", revision_index, revision),
                    "path": f"/images/{image_index}/photo",
                    "photo": photo_id,
                    "content_digest": expected[photo_id][0],
                    "conditions": facts,
                }
            )
    body = unseal(baseline.encrypted_selection)
    row = save_selection(
        author,
        case.pk,
        case.version,
        baseline.assessment_review_id,
        uuid4(),
        baseline.version,
        reason,
        body["selection"],
        field_evidence=body["field_evidence"],
        images=decisions,
    )
    reviewer = previous.action.actor
    record(reviewer, case.pk, case.version, row.pk, uuid4(), reason)
    for photo_id in expected:
        _, content = inspect(reviewer, case.pk, case.version, row.pk, photo_id, uuid4(), reason)
        assert hashlib.sha256(content).hexdigest() == expected[photo_id][0]
    decision, _ = record(
        reviewer, case.pk, case.version, row.pk, uuid4(), reason, "review", "approved"
    )
    version = case.version
    tracemalloc.start()
    started = time.perf_counter()
    try:
        export = generate(author, case.pk, version, row.pk, decision.pk, uuid4(), reason)
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    record_property("generation_seconds", elapsed)
    record_property("generation_python_peak_bytes", peak)
    record_property("source_image_bytes", sum(size for _, size in expected.values()))
    assert export.images.count() == 8 and export.parts.count() >= 2
    mapping = dict(export.images.values_list("pk", "photo_id"))
    public = Client()
    recovered = {}
    for part in export.parts.order_by("position"):
        response = public.post(url(receipt, export) + f"part/{part.pk}/", {"key": uuid4()})
        assert response.status_code == 200 and len(response.content) <= 64 * 1024 * 1024
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for name in archive.namelist():
                attachment = next(
                    identifier for identifier in mapping if str(identifier) == name[:-5]
                )
                photo_id = str(mapping[attachment])
                assert photo_id not in recovered
                recovered[photo_id] = hashlib.sha256(archive.read(name)).hexdigest()
    assert recovered == {photo: digest for photo, (digest, _) in expected.items()}
    assert public.post(url(receipt, export), {"key": uuid4()}).json()["images"]
    case.refresh_from_db()
    assert case.version == version + 1 and case.status == "reviewing"
