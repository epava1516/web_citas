import hashlib
import io
import uuid
import warnings
from dataclasses import asdict
from datetime import timedelta

import cv2
import imagehash
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.core.verification import locked_manager_person
from apps.listings.history import is_rectification_history, rectification_history_ids
from apps.listings.models import Revision

from .models import Blob, Match, Photo, UploadAttempt
from .similarity import Signature, compare_signatures, compute_signature, confirm_match

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000


@sensitive_variables()
def decode_image(raw):
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        image = Image.open(io.BytesIO(raw))
        if image.format not in {"JPEG", "PNG", "WEBP"} or getattr(image, "is_animated", False):
            raise ValidationError("Only static JPEG/PNG/WebP images are allowed")
        if image.width * image.height > MAX_PIXELS:
            raise ValidationError("Image exceeds forty megapixels")
        image.verify()
        image = Image.open(io.BytesIO(raw))
        image.load()
        return ImageOps.exif_transpose(image).convert("RGB")


@sensitive_variables()
def read_upload(upload):
    if upload.size > MAX_BYTES:
        raise ValidationError("Image exceeds ten MiB")
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError("Image exceeds ten MiB")
    try:
        image = decode_image(raw)
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValidationError("Invalid or unsafe image") from error
    sha = hashlib.sha256(raw).hexdigest()
    return raw, image, sha


def ingest(user, revision_id, upload):
    raw, image, sha = read_upload(upload)
    written = None
    try:
        with transaction.atomic():
            initial = Revision.objects.get(pk=revision_id)
            person = locked_manager_person(user, initial.listing.person_id)
            revision = Revision.objects.select_for_update().get(pk=revision_id)
            if (
                is_rectification_history(revision)
                or revision.status != "draft"
                or revision.manager_version != person.manager_version
                or revision.photos.filter(rectification_upload__isnull=False).exists()
            ):
                raise ValidationError("Revision is no longer editable")
            existing = revision.photos.filter(blob__sha256=sha, removed_at__isnull=True).first()
            if existing:
                UploadAttempt.objects.create(user=user, revision=revision, result="repeat")
                return existing
            if revision.photos.filter(removed_at__isnull=True).count() >= 8:
                raise ValidationError("Maximum eight photos")
            blob, created = Blob.objects.get_or_create(sha256=sha)
            blob = Blob.objects.select_for_update().get(pk=blob.pk)
            if blob.status in {"erasing", "erased", "purging", "purged"}:
                raise ValidationError("Image unavailable during erasure")
            if created:
                blob.width, blob.height = image.size
                blob.original.save(str(uuid.uuid4()), ContentFile(raw), save=False)
                written = blob.original.name
                blob.save()
            photo = Photo.objects.create(
                revision=revision,
                blob=blob,
                position=revision.photos.filter(removed_at__isnull=True).count(),
            )
            # Exact candidates are global, never limited to contact or agency.
            for candidate in (
                Photo.objects.filter(blob=blob, removed_at__isnull=True)
                .exclude(revision_id__in=rectification_history_ids())
                .exclude(revision__status="rights-stage")
                .exclude(rectification_upload__isnull=False)
                .exclude(revision__listing__person_id=person.pk)
            ):
                Match.objects.get_or_create(
                    photo=photo, candidate=candidate, defaults={"method": "sha256"}
                )
            UploadAttempt.objects.create(
                user=user,
                revision=revision,
                result="duplicate" if photo.matches.exists() else "accepted",
            )
            revision.edit_version += 1
            revision.save(update_fields=["edit_version", "updated_at"])
            from .tasks import process_blob

            transaction.on_commit(lambda: process_blob.delay(str(blob.pk)), robust=True)
            return photo
    except Exception:
        if written:
            Blob._meta.get_field("original").storage.delete(written)
        raise


def process(blob_id):
    ready = False
    with transaction.atomic():
        blob = Blob.objects.select_for_update().get(pk=blob_id)
        if blob.status in {"erasing", "erased", "purging", "purged"}:
            return
        ready = blob.status == "ready"
        if not ready:
            if (
                blob.status == "processing"
                and blob.started_at
                and blob.started_at > timezone.now() - timedelta(minutes=3)
            ):
                return
            blob.status = "processing"
            blob.started_at = timezone.now()
            blob.attempts += 1
            blob.save(update_fields=["status", "started_at", "attempts"])
    if ready:
        detect_matches(blob_id)
        return
    try:
        with blob.original.open("rb") as source:
            image = decode_image(source.read(MAX_BYTES + 1))
        image.thumbnail((1600, 1600))
        cv2.setNumThreads(1)
        signature = compute_signature(image)
        phash = str(imagehash.phash(image))
        regions = [f"{value:016x}" for _, value in signature.window_hashes]
        output = io.BytesIO()
        image.info.clear()
        image.save(output, format="WEBP", quality=85, method=4)
        with transaction.atomic():
            blob = Blob.objects.select_for_update().get(pk=blob_id)
            if blob.status in {"erasing", "erased", "purging", "purged"}:
                return
            blob.derivative.save(
                str(uuid.uuid4()) + ".webp", ContentFile(output.getvalue()), save=False
            )
            blob.phash, blob.regional_hashes, blob.status = phash, regions, "ready"
            blob.signature = asdict(signature)
            blob.error_code = ""
            blob.save()
        detect_matches(blob_id)
    except (OSError, ValidationError, UnidentifiedImageError, Image.DecompressionBombError):
        Blob.objects.filter(pk=blob_id).exclude(
            status__in=["erasing", "erased", "purging", "purged"]
        ).update(status="failed", error_code="decode_or_storage_failed")
        raise


def stored_signature(blob):
    values = dict(blob.signature)
    if not values:
        return None
    values["rotated_hashes"] = tuple(values["rotated_hashes"])
    values["window_hashes"] = tuple((tuple(item[0]), item[1]) for item in values["window_hashes"])
    return Signature(**values)


def record_match(photo, candidate, defaults):
    # Erasure and uploads serialize on Blob. Order both IDs to avoid pair inversion.
    with transaction.atomic():
        blobs = list(
            Blob.objects.select_for_update()
            .filter(pk__in=[photo.blob_id, candidate.blob_id])
            .order_by("pk")
        )
        if Photo.objects.filter(pk=candidate.pk, rectification_upload__isnull=False).exists():
            return
        if Photo.objects.filter(pk=candidate.pk, revision__status="rights-stage").exists():
            return
        if Photo.objects.filter(
            pk__in=[photo.pk, candidate.pk], revision_id__in=rectification_history_ids()
        ).exists():
            return
        if any(blob.status in {"erasing", "erased", "purging", "purged"} for blob in blobs):
            return
        if Photo.objects.filter(pk__in=[photo.pk, candidate.pk], removed_at__isnull=False).exists():
            return
        Match.objects.get_or_create(photo=photo, candidate=candidate, defaults=defaults)


def detect_matches(blob_id):
    blob = Blob.objects.get(pk=blob_id)
    photos_to_compare = list(
        blob.photos.filter(removed_at__isnull=True)
        .exclude(revision_id__in=rectification_history_ids())
        .select_related("revision__listing")
    )
    if not photos_to_compare:
        return
    from apps.safety.photo_reintroduction import detect as detect_reintroduction

    for photo in photos_to_compare:
        detect_reintroduction(photo.pk)
    signature = stored_signature(blob)
    if not signature:
        return
    candidates = (
        Photo.objects.filter(removed_at__isnull=True)
        .exclude(revision_id__in=rectification_history_ids())
        .exclude(revision__status="rights-stage")
        .exclude(rectification_upload__isnull=False)
    )
    # Reused bytes (including cloned revisions) need global exact candidates too.
    for photo in photos_to_compare:
        for candidate in candidates.filter(blob=blob).exclude(
            revision__listing__person_id=photo.revision.listing.person_id
        ):
            record_match(photo, candidate, {"method": "sha256"})
    image = None
    for other in (
        Blob.objects.filter(status="ready", photos__in=candidates)
        .exclude(pk=blob.pk)
        .distinct()
        .iterator()
    ):
        other_signature = stored_signature(other)
        if not other_signature:
            continue
        candidate_result = compare_signatures(signature, other_signature)
        if not candidate_result.is_candidate:
            continue
        if image is None:
            with blob.derivative.open("rb") as source:
                image = Image.open(source).convert("RGB")
        with other.derivative.open("rb") as source:
            other_image = Image.open(source).convert("RGB")
        confirmation = confirm_match(image, other_image)
        method = "orb" if confirmation.status == "confirmed" else "regional"
        score = confirmation.inlier_ratio if method == "orb" else 1 - candidate_result.distance / 64
        for photo in photos_to_compare:
            for candidate in candidates.filter(blob=other).exclude(
                revision__listing__person_id=photo.revision.listing.person_id
            ):
                record_match(photo, candidate, {"method": method, "score": score})

    blob.photos.filter(
        pk__in=[photo.pk for photo in photos_to_compare], removed_at__isnull=True
    ).update(comparison_complete=True)
