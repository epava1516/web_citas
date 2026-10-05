"""Audited metadata pages for omitted binaries; does not authorize image bytes."""

from copy import deepcopy
from uuid import UUID, uuid5

from cryptography.fernet import InvalidToken
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverage, RightsPortabilitySelectionReview
from .rights import fingerprint
from .rights_copy_inspection import SECTIONS
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_pages import MAX_AGE, baseline_body, latest
from .rights_portability_coverage_store import save_coverage
from .rights_portability_selected_use import consume_selected

SALT = "portability-coverage-images-v1"
PAGE_SIZE = 20


@transaction.atomic
@sensitive_variables()
def prepare_images(
    user, case_id, version, review_id, key, purpose, page=1, *, baseline_id=None, use_latest=True
):
    if type(page) is not int or page < 1:
        raise ValidationError("Invalid omitted image page")
    case, person, listing = reviewer_case(user, case_id)
    decision = (
        RightsPortabilitySelectionReview.objects.select_related("read__action", "action")
        .filter(pk=review_id, selection__request=case, selection__actor=user)
        .first()
    )
    if decision is None:
        raise ValidationError("Own approved selection required")
    selection, _ = consume_selected(
        user,
        case_id,
        version,
        decision.selection_id,
        decision.pk,
        uuid5(key, f"coverage-images:{page}"),
        purpose,
    )
    facts = unseal(selection.encrypted_selection)
    assessment = unseal(selection.assessment_review.assessment.encrypted_assessment)
    source = source_copy(person, listing, case)
    if fingerprint(canonical(source)) != selection.source_digest:
        raise ValidationError("Coverage image source changed")
    baseline = (
        latest(case, user)
        if baseline_id is None and use_latest
        else (
            RightsPortabilityCoverage.objects.filter(
                pk=baseline_id, request=case, actor=user
            ).first()
        )
    )
    if baseline_id is not None and baseline is None:
        raise ValidationError("Coverage baseline unavailable")
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "actor": user.pk,
                "version": version,
                "selection": selection.pk,
                "review": decision.pk,
                "proof": str(selection.proof_id),
                "source": selection.source_digest,
                "selection_digest": selection.selection_digest,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "page": page,
                "purpose": purpose,
                "baseline": baseline.pk if baseline else None,
                "baseline_digest": baseline.coverage_digest if baseline else None,
                "baseline_ciphertext": fingerprint(baseline.encrypted_coverage)
                if baseline
                else None,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    if action is None:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=user,
                    operation="coverage_images",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": purpose}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage image key") from error
    if (
        action.request_id,
        action.actor_id,
        action.operation,
        action.expected_version,
        action.payload_digest,
    ) != (case.pk, user.pk, "coverage_images", version, signature):
        raise ValidationError("Conflicting coverage image key")
    try:
        if unseal(action.encrypted_reason) != {"reason": purpose}:
            raise ValidationError("Coverage image purpose changed")
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage image purpose unavailable") from error
    body = (
        baseline_body(baseline, case, user, selection, decision)
        if baseline
        else {"omissions": {name: {} for name in SECTIONS}, "image_omissions": {}}
    )
    compile_coverage(
        source,
        assessment,
        facts["selection"],
        body["omissions"],
        facts.get("images", []),
        body["image_omissions"],
        field_evidence=facts.get("field_evidence"),
        allow_partial=True,
    )
    included = {item["photo"] for item in facts.get("images", [])}
    candidates = (
        []
        if assessment["revisions"]["status"] == "excluded"
        else [
            deepcopy(image)
            for row in source["revisions"]
            for image in row["images"]
            if image["photo"] not in included
        ]
    )
    start = (page - 1) * PAGE_SIZE
    images = candidates[start : start + PAGE_SIZE]
    if page > 1 and not images:
        raise ValidationError("Omitted image page unavailable")
    token = signing.dumps(
        {
            "actor": user.pk,
            "case": str(case.pk),
            "version": version,
            "session": user.session_version,
            "mfa": user.mfa_version,
            "review": review_id,
            "key": str(key),
            "purpose": purpose,
            "page": page,
            "photos": [item["photo"] for item in images],
            "base_id": baseline.pk if baseline else None,
            "base_version": baseline.version if baseline else 0,
            "base_digest": baseline.coverage_digest if baseline else None,
        },
        salt=SALT,
        compress=True,
    )
    fresh_authority(user, case, user.session_version, user.mfa_version)
    if (
        can_prepare(User.objects.get(pk=user.pk), case, person).pk != selection.proof_id
        or fingerprint(canonical(source_copy(person, listing, case))) != selection.source_digest
    ):
        raise ValidationError("Coverage image authority or source changed")
    return {
        "token": token,
        "images": images,
        "page": page,
        "count": len(candidates),
        "has_next": start + PAGE_SIZE < len(candidates),
        "decisions": {
            item["photo"]: body["image_omissions"][item["photo"]]
            for item in images
            if item["photo"] in body["image_omissions"]
        },
    }


@transaction.atomic
@sensitive_variables()
def save_images(user, case_id, token, key, reason, decisions):
    try:
        context = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except (signing.BadSignature, ValueError, TypeError) as error:
        raise ValidationError("Omitted image page expired or invalid") from error
    if not isinstance(context, dict) or (
        context.get("actor") != user.pk
        or context.get("case") != str(case_id)
        or context.get("session") != user.session_version
        or context.get("mfa") != user.mfa_version
    ):
        raise PermissionDenied
    if not isinstance(decisions, dict) or not set(decisions) <= set(context["photos"]):
        raise ValidationError("Decide only omitted images from inspected page")
    case, _, _ = reviewer_case(user, case_id)
    current = latest(case, user)
    retry = RightsPortabilityCoverage.objects.filter(
        action__key=key, request=case, actor=user
    ).first()
    if retry is None and (current.pk if current else None) != context["base_id"]:
        raise ValidationError("Coverage version changed")
    page = prepare_images(
        user,
        case_id,
        context["version"],
        context["review"],
        UUID(context["key"]),
        context["purpose"],
        context["page"],
        baseline_id=context["base_id"],
        use_latest=False,
    )
    if [item["photo"] for item in page["images"]] != context["photos"]:
        raise ValidationError("Omitted image page changed")
    base = RightsPortabilityCoverage.objects.filter(pk=context["base_id"]).first()
    if base and (
        base.version != context["base_version"] or base.coverage_digest != context["base_digest"]
    ):
        raise ValidationError("Coverage baseline changed")
    body = (
        unseal(base.encrypted_coverage)
        if base
        else {"omissions": {name: {} for name in SECTIONS}, "image_omissions": {}}
    )
    omissions = deepcopy(body["image_omissions"])
    for photo in context["photos"]:
        omissions.pop(photo, None)
    omissions.update(deepcopy(decisions))
    return save_coverage(
        user,
        case_id,
        context["version"],
        context["review"],
        key,
        context["base_version"],
        reason,
        deepcopy(body["omissions"]),
        omissions,
        allow_partial=True,
    )
