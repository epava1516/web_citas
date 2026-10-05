"""Signed guided binary selection; preserves scalar choices and other image declarations."""

import hashlib
from copy import deepcopy
from uuid import UUID

from cryptography.fernet import InvalidToken
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import unseal
from .models import RightsAction, RightsImageAccess, RightsPortabilitySelection
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import canonical, image_content, reviewer_case, source_copy
from .rights_portability_page_selection import latest_draft
from .rights_portability_selection import row_reference
from .rights_portability_selection_store import save_selection, validate_selection_evidence
from .rights_portability_use import consume_approved

SALT = "portability-binary-page-v1"
MAX_AGE = 1800


@transaction.atomic
@sensitive_variables()
def catalog(user, case_id, version, review_id, key, purpose, revision_index, image_index):
    if (
        type(revision_index) is not int
        or revision_index < 0
        or type(image_index) is not int
        or image_index < 0
        or not isinstance(purpose, str)
        or not 20 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError("Invalid portable image page")
    case, person, listing = reviewer_case(user, case_id)
    fresh_authority(user, case, user.session_version, user.mfa_version)
    review, assessment = consume_approved(
        user,
        case_id,
        version,
        review_id,
        key,
        purpose,
        selection_binding=fingerprint(
            canonical({"revision": revision_index, "image": image_index})
        ),
        audit_operation="image_catalog",
    )
    if not person or assessment["revisions"]["status"] not in {"eligible", "granular"}:
        raise ValidationError("Eligible profile revision assessment required")
    source = source_copy(person, listing, case)
    revisions = source["revisions"]
    if revision_index >= len(revisions):
        raise ValidationError("Portable revision unavailable")
    revision = revisions[revision_index]
    if image_index >= len(revision["images"]):
        raise ValidationError("Portable image unavailable")
    photo, content = image_content(person, revision["images"][image_index]["photo"])
    digest = hashlib.sha256(content).hexdigest()
    RightsImageAccess.objects.get_or_create(
        request=case,
        actor=user,
        photo=photo,
        case_version=version,
        content_digest=digest,
        purpose=purpose,
    )
    declaration = {
        "row": row_reference("revisions", revision_index, revision),
        "path": f"/images/{image_index}/photo",
        "photo": str(photo.pk),
        "content_digest": digest,
    }
    fresh_authority(user, case, user.session_version, user.mfa_version)
    return case, review, assessment, declaration, content


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, version, review_id, key, purpose, revision_index, image_index):
    case, review, _, declaration, content = catalog(
        user, case_id, version, review_id, key, purpose, revision_index, image_index
    )
    baseline = latest_draft(case, user)
    existing = None
    if baseline:
        body = validate_selection_evidence(baseline, review, case)
        existing = next(
            (item for item in body.get("images", []) if item["photo"] == declaration["photo"]), None
        )
    context = {
        "actor": user.pk,
        "case": str(case.pk),
        "version": version,
        "session": user.session_version,
        "mfa": user.mfa_version,
        "review": review_id,
        "catalog_key": str(key),
        "revision": revision_index,
        "image": image_index,
        "declaration": declaration,
        "baseline": baseline.pk if baseline else None,
        "baseline_version": baseline.version if baseline else 0,
        "baseline_digest": baseline.selection_digest if baseline else None,
    }
    return {
        "token": signing.dumps(context, salt=SALT),
        "declaration": declaration,
        "content": content,
        "conditions": existing["conditions"] if existing else None,
        "included": existing is not None,
    }


@transaction.atomic
@sensitive_variables()
def save(user, key, token, reason, included, conditions, *, path=None):
    try:
        context = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature as error:
        raise ValidationError("Portable image form changed or expired") from error
    if not isinstance(context, dict):
        raise ValidationError("Portable image form unavailable")
    if (
        type(included) is not bool
        or context.get("actor") != user.pk
        or context.get("session") != user.session_version
        or context.get("mfa") != user.mfa_version
    ):
        raise PermissionDenied
    case, _, _ = reviewer_case(user, context["case"])
    fresh_authority(user, case, user.session_version, user.mfa_version)
    original = RightsAction.objects.filter(
        key=context["catalog_key"],
        request=case,
        actor=user,
        operation="image_catalog",
        expected_version=context["version"],
    ).first()
    if not original:
        raise ValidationError("Audited portable image page required")
    try:
        purpose = unseal(original.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Portable image page unavailable") from error
    _, review, assessment, declaration, _ = catalog(
        user,
        case.pk,
        context["version"],
        context["review"],
        UUID(context["catalog_key"]),
        purpose,
        context["revision"],
        context["image"],
    )
    if declaration != context["declaration"]:
        raise ValidationError("Portable image content or source changed")
    if path is not None and path != declaration["path"]:
        raise ValidationError("Portable image field path changed")
    baseline = None
    if context["baseline"]:
        baseline = RightsPortabilitySelection.objects.filter(
            pk=context["baseline"],
            request=case,
            actor=user,
            version=context["baseline_version"],
            selection_digest=context["baseline_digest"],
        ).first()
        if baseline is None:
            raise ValidationError("Portable image baseline changed")
    previous = RightsAction.objects.filter(key=key).first()
    latest = latest_draft(case, user)
    if not previous and (latest.pk if latest else None) != context["baseline"]:
        raise ValidationError("Portable image baseline changed")
    if baseline:
        body = validate_selection_evidence(baseline, review, case)
        selectors = deepcopy(body["selection"])
        evidence = deepcopy(body.get("field_evidence"))
        images = deepcopy(body.get("images", []))
    else:
        selectors = {
            name: []
            for name, facts in assessment.items()
            if facts["status"] in {"eligible", "granular"}
        }
        evidence, images = None, []
    images = [item for item in images if item["photo"] != declaration["photo"]]
    if included:
        images.append({**declaration, "conditions": conditions})
    return save_selection(
        user,
        case.pk,
        context["version"],
        review.pk,
        key,
        context["baseline_version"],
        reason,
        selectors,
        field_evidence=evidence,
        images=images,
    )
