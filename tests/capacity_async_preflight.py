"""One finite real worker/S3 generation; never a capacity sample."""

import hashlib
import io
import random
import time
from uuid import uuid4

import test_rights_portability_export_races as fixtures
from capacity_delivery_flow import queued_generation
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.core.models import User
from apps.mediafiles.models import Blob, Photo
from apps.safety.crypto import unseal
from apps.safety.object_storage.repository import PREFIX
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import image_content, reviewer_case, source_copy
from apps.safety.rights_object_content import image_bytes
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_export import validate_export_binding
from apps.safety.rights_portability_selection import row_reference

REASON = "Inspect original synthetic coverage for finite asynchronous preflight"


def prepare(request, settings, monkeypatch):
    """Own subject/blob, built before assessment; all approvals use normal services."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    original = fixtures.ready

    def with_large_binary(*args, **kwargs):
        result = original(*args, **(kwargs | {"subject_username": "fixture-v1-model-b"}))
        case, author, *_, person = result
        with transaction.atomic():
            locked, person, listing = reviewer_case(author, case.pk)
            initial = source_copy(person, listing, locked)
        photo = Photo.objects.get(pk=initial["revisions"][0]["images"][0]["photo"])
        width, height = 1024, 1400
        bitmap = Image.frombytes("RGB", (width, height),
                                 random.Random("mod08-finite-worker-probe").randbytes(width * height * 3))
        output = io.BytesIO()
        bitmap.save(output, format="WEBP", lossless=True, method=0)
        content = output.getvalue()
        assert 4 * 1024 ** 2 <= len(content) < 10 * 1024 ** 2
        with Image.open(io.BytesIO(content)) as decoded:
            decoded.load()
            assert decoded.size == (width, height) and decoded.format == "WEBP"
        blob = Blob.objects.create(sha256=hashlib.sha256(content).hexdigest(),
                                   width=width, height=height, status="ready")
        blob.original.save(str(uuid4()) + ".webp", ContentFile(content))
        blob.derivative.save(str(uuid4()) + ".webp", ContentFile(content))
        # New files belong only to the disposable fixture, never shared source bytes.
        photo.blob = blob
        photo.save(update_fields=["blob"])
        return result

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "ready", with_large_binary)
        case, author, selection, selected, _, _, _ = prepared_covered_selection(
            request, settings, patch, False, binary=True)
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    chosen = unseal(selection.encrypted_selection)
    assert len(chosen["images"]) == 1
    facts = dict(status="excluded", basis="other", origin="inferred", automated=True,
                 subject_related=True, third_party_reviewed=True, reason=REASON,
                 evidence="Documented synthetic finite preflight exclusion")
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        for index, item in enumerate(reader(source)):
            reference = row_reference(dataset, index, item)
            fields = next((set(row["fields"]) for row in chosen["selection"][dataset]
                           if row["row"] == reference), set())
            if any(field["path"] not in fields for field in scalar_fields(item)):
                omissions[dataset][reference] = {"all": facts}
    included = {image["photo"] for image in chosen["images"]}
    omitted_images = {image["photo"]: facts for revision in source["revisions"]
                      for image in revision["images"] if image["photo"] not in included}
    coverage = save_coverage(author, case.pk, case.version, selected.pk, uuid4(), 0,
                             REASON, omissions, omitted_images)
    reviewer = User.objects.get(pk=selected.action.actor_id)
    required = required_pages(source)
    for dataset, index, page, binary in required:
        inspect_page(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON,
                     dataset, index, page, binary=binary)
    reviewed = record(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "approved")
    assert len(reviewed.read_ids) == len(required)
    settings.CELERY_TASK_ALWAYS_EAGER = False
    return case, author, selected, reviewed, chosen["images"][0]


def run(prepared, endpoint, settings, metrics):
    case, author, selected, coverage, declaration = prepared
    assert settings.CELERY_TASK_ALWAYS_EAGER is False
    assert settings.RIGHTS_OBJECT_STORAGE_ENABLED
    begin = time.perf_counter()
    export = queued_generation(case, author, selected, coverage, endpoint, settings,
                               metrics, observation_timeout=180)
    snapshots = list(export.images.all())
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.encrypted_content.startswith(PREFIX)
    content = image_bytes(snapshot)
    assert len(content) >= 4 * 1024 ** 2
    assert str(snapshot.photo_id) == declaration["photo"]
    assert hashlib.sha256(content).hexdigest() == declaration["content_digest"]
    assert export.parts.exists()
    assert all(part.encrypted_content.startswith(PREFIX) for part in export.parts.all())
    case.refresh_from_db()
    with transaction.atomic():
        locked, person, _ = reviewer_case(author, case.pk)
        _, current = image_content(person, declaration["photo"])
        assert current == content
        validate_export_binding(locked, person, export)
    metrics.update(success=True, image_bytes=len(content), image_sha256=declaration["content_digest"],
                   observation_seconds=time.perf_counter() - begin,
                   normal_generation_objective_seconds=120,
                   scope="One small synthetic real Celery/LOGIN/S3 generation; no capacity verdict")
