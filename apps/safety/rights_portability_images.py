"""Explicit binary image eligibility; metadata selection alone never authorizes bytes."""

import re
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from .rights_portability import DATASETS, checked_assessment
from .rights_portability_selection import row_reference

IMAGE_PATH = re.compile(r"/images/(0|[1-9][0-9]*)/photo\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@sensitive_variables()
def checked_images(source, assessment, decisions, inspected_digests):
    """Validate declarations against caller-audited content; grants no access itself."""
    assessed = checked_assessment(assessment)
    if not isinstance(decisions, list) or not isinstance(inspected_digests, dict):
        raise ValidationError("Invalid portable image declarations")
    if decisions and assessed["revisions"]["status"] not in {"eligible", "granular"}:
        raise ValidationError("Portable revision assessment required")
    rows = source.get("revisions", [])
    if not isinstance(rows, list):
        raise ValidationError("Portable revision source unavailable")
    references = {row_reference("revisions", index, row): row for index, row in enumerate(rows)}
    seen, checked = set(), []
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision) != {
            "row",
            "path",
            "photo",
            "content_digest",
            "conditions",
        }:
            raise ValidationError("Exact portable image declaration required")
        ref, path, photo, digest = (
            decision["row"],
            decision["path"],
            decision["photo"],
            decision["content_digest"],
        )
        if (
            not isinstance(ref, str)
            or ref not in references
            or not isinstance(path, str)
            or len(path) > 500
            or not isinstance(photo, str)
            or photo in seen
            or not isinstance(digest, str)
            or not DIGEST.fullmatch(digest)
        ):
            raise ValidationError("Portable image reference unavailable")
        matched = IMAGE_PATH.fullmatch(path)
        images = references[ref].get("images")
        if not matched or not isinstance(images, list) or int(matched[1]) >= len(images):
            raise ValidationError("Portable image path unavailable")
        image = images[int(matched[1])]
        if (
            not isinstance(image, dict)
            or image.get("photo") != photo
            or image.get("processing_status") != "ready"
        ):
            raise ValidationError("Portable image source changed")
        if inspected_digests.get(photo) != digest:
            raise ValidationError("Inspect exact portable image content first")
        conditions = decision["conditions"]
        if not isinstance(conditions, dict) or conditions.get("status") != "eligible":
            raise ValidationError("Portable image conditions required")
        checked_assessment({name: conditions for name in DATASETS})
        seen.add(photo)
        checked.append(deepcopy(decision))
    if set(inspected_digests) != seen:
        raise ValidationError("Image inspections must match the selected binaries")
    return checked


@sensitive_variables()
def audited_images(actor, case, person, source, assessment, decisions):
    """Recheck current binary bytes against the preparer's existing private inspection."""
    import hashlib

    from django.db import transaction

    from .models import RightsImageAccess
    from .rights_exports import image_content

    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Portable image evidence requires enclosing transaction")
    if not isinstance(decisions, list):
        raise ValidationError("Invalid portable image declarations")
    declared = {}
    for decision in decisions:
        if not isinstance(decision, dict) or not isinstance(decision.get("photo"), str):
            raise ValidationError("Invalid portable image declarations")
        declared[decision["photo"]] = decision.get("content_digest")
    cleaned = checked_images(source, assessment, decisions, declared)
    for decision in cleaned:
        photo, content = image_content(person, decision["photo"])
        digest = hashlib.sha256(content).hexdigest()
        if (
            digest != decision["content_digest"]
            or not RightsImageAccess.objects.filter(
                request=case,
                actor=actor,
                photo=photo,
                case_version=case.version,
                content_digest=digest,
            ).exists()
        ):
            raise ValidationError("Inspect exact portable image content first")
    return cleaned
