"""Own audited, signed scalar omission pages; never independent review or closure."""

from copy import deepcopy
from itertools import islice
from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverage
from .rights import fingerprint
from .rights_copy_inspection import SECTIONS
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_inspection_source import inspection_source, shared_source
from .rights_portability_catalog import FIELD_PAGE_SIZE, scalar_fields
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_store import save_coverage
from .rights_portability_selected_use import consume_selected
from .rights_portability_selection import row_reference

SALT = "portability-coverage-page-v1"
MAX_AGE = 1800


def recheck_authority(user, case, person, proof_id):
    fresh_authority(user, case, user.session_version, user.mfa_version)
    if can_prepare(User.objects.get(pk=user.pk), case, person).pk != proof_id:
        raise ValidationError("Coverage page authority changed before return")


def latest(case, actor):
    return (
        RightsPortabilityCoverage.objects.filter(request=case, actor=actor)
        .order_by("-version")
        .first()
    )


@sensitive_variables()
def baseline_body(row, case, actor, selection, decision):
    """Call only after audited current selection consumption in a locked transaction."""
    if row.purged_at or row.expires_at <= timezone.now():
        raise ValidationError("Coverage baseline expired")
    try:
        body = unseal(row.encrypted_coverage)
        reason = unseal(row.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Coverage baseline unavailable") from error
    if not isinstance(body, dict):
        raise ValidationError("Coverage baseline unavailable")
    digest = fingerprint(canonical(body))
    signature = fingerprint(
        canonical(
            {
                "case_version": case.version,
                "proof": str(selection.proof_id),
                "body": digest,
                "reason": reason,
            }
        )
    )
    if (
        row.request_id != case.pk
        or row.actor_id != actor.pk
        or row.action.request_id != case.pk
        or row.action.actor_id != actor.pk
        or row.action.operation != "coverage_save"
        or row.action.expected_version != case.version
        or row.action.payload_digest != signature
        or row.coverage_digest != digest
        or row.selection_review_id != decision.pk
        or row.proof_id != selection.proof_id
        or row.source_digest != selection.source_digest
        or row.selection_digest != selection.selection_digest
        or row.original_session_version != actor.session_version
        or row.original_mfa_version != actor.mfa_version
        or body.get("schema") != "portability-coverage-draft-v1"
        or body.get("version") != row.version - 1
        or body.get("selection") != selection.pk
        or body.get("review") != decision.pk
        or body.get("source") != selection.source_digest
        or body.get("selection_digest") != selection.selection_digest
        or body.get("selection_ciphertext") != fingerprint(selection.encrypted_selection)
        or body.get("inspection") != decision.read.action.payload_digest
        or body.get("decision") != decision.action.payload_digest
        or body.get("session") != actor.session_version
        or body.get("mfa") != actor.mfa_version
        or type(body.get("allow_partial", False)) is not bool
    ):
        raise ValidationError("Coverage baseline changed")
    return body


@transaction.atomic
@sensitive_variables()
def prepare_page(
    user,
    case_id,
    version,
    review_id,
    key,
    purpose,
    dataset,
    row_index=0,
    field_page=1,
    *,
    baseline_id=None,
    use_latest=True,
):
    check_page_arguments(dataset, row_index, field_page)
    case, person, listing = reviewer_case(user, case_id)
    # One audited source for every nested check; its exit compares against fresh DB rows
    # inside this transaction, then authority is rechecked after that potentially long read.
    with inspection_source(person, listing, case) as context:
        result, proof_id = _prepare_page(
            user, case_id, version, review_id, key, purpose, dataset, row_index, field_page,
            baseline_id=baseline_id, use_latest=use_latest, _inspection_source=context,
        )
    recheck_authority(user, case, person, proof_id)
    return result


def check_page_arguments(dataset, row_index, field_page):
    if (
        not isinstance(dataset, str)
        or dataset not in SECTIONS
        or type(row_index) is not int
        or row_index < 0
        or (type(field_page) is not int or field_page < 1)
    ):
        raise ValidationError("Invalid coverage page")


@sensitive_variables()
def _prepare_page(
    user, case_id, version, review_id, key, purpose, dataset, row_index, field_page, *,
    baseline_id, use_latest, _inspection_source,
):
    """Caller owns the enclosing transaction and the active inspection source context."""
    check_page_arguments(dataset, row_index, field_page)
    case, person, listing = reviewer_case(user, case_id)

    def current_source():
        return shared_source(_inspection_source, person, listing, case)

    from .models import RightsPortabilitySelectionReview

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
        uuid5(key, f"coverage-page:{dataset}:{row_index}:{field_page}"),
        purpose,
        _inspection_source=_inspection_source,
    )
    facts = unseal(selection.encrypted_selection)
    assessment = unseal(selection.assessment_review.assessment.encrypted_assessment)
    source = current_source()
    if fingerprint(canonical(source)) != selection.source_digest:
        raise ValidationError("Coverage source changed")
    if assessment[dataset]["status"] == "excluded":
        raise ValidationError("Excluded dataset needs no scalar omission page")
    baseline = (
        latest(case, user)
        if baseline_id is None and use_latest
        else RightsPortabilityCoverage.objects.filter(
            pk=baseline_id, request=case, actor=user
        ).first()
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
                "dataset": dataset,
                "row": row_index,
                "field_page": field_page,
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
                    operation="coverage_page",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": purpose}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage page key") from error
    if (
        action.request_id,
        action.actor_id,
        action.operation,
        action.expected_version,
        action.payload_digest,
    ) != (case.pk, user.pk, "coverage_page", version, signature):
        raise ValidationError("Conflicting coverage page key")
    try:
        if unseal(action.encrypted_reason) != {"reason": purpose}:
            raise ValidationError("Coverage page reason changed")
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage page reason unavailable") from error
    # The exact baseline/ciphertext/page are audited before any coverage is decrypted.
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
    rows = SECTIONS[dataset](source)
    if row_index >= len(rows):
        raise ValidationError("Coverage row unavailable")
    row = rows[row_index]
    reference = row_reference(dataset, row_index, row)
    selected = next(
        (
            set(item["fields"])
            for item in facts["selection"].get(dataset, [])
            if item["row"] == reference
        ),
        set(),
    )
    candidates = (item for item in scalar_fields(row) if item["path"] not in selected)
    start = (field_page - 1) * FIELD_PAGE_SIZE
    fields = list(islice(candidates, start, start + FIELD_PAGE_SIZE + 1))
    if field_page > 1 and not fields:
        raise ValidationError("Coverage field page unavailable")
    more = len(fields) > FIELD_PAGE_SIZE
    fields = fields[:FIELD_PAGE_SIZE]
    previous = body["omissions"][dataset].get(reference, {})
    decisions = previous.get("fields", {})
    if "all" in previous:
        decisions = {
            item["path"]: previous["all"]
            for item in scalar_fields(row)
            if item["path"] not in selected
        }
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
            "dataset": dataset,
            "row_index": row_index,
            "field_page": field_page,
            "row": reference,
            "paths": [item["path"] for item in fields],
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
        or fingerprint(canonical(current_source())) != selection.source_digest
    ):
        raise ValidationError("Coverage page authority or source changed")
    return {
        "token": token,
        "dataset": dataset,
        "row": reference,
        "row_index": row_index,
        "row_count": len(rows),
        "field_page": field_page,
        "fields": fields,
        "has_next_fields": more,
        "has_next_row": row_index + 1 < len(rows),
        "row_decisions": decisions,
        "decisions": {
            item["path"]: decisions[item["path"]] for item in fields if item["path"] in decisions
        },
    }, selection.proof_id


@transaction.atomic
@sensitive_variables()
def save_page(user, case_id, token, key, reason, decisions):
    try:
        context = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except (signing.BadSignature, TypeError, ValueError) as error:
        raise ValidationError("Coverage page expired or invalid") from error
    if not isinstance(context, dict) or (
        context.get("actor") != user.pk
        or context.get("case") != str(case_id)
        or context.get("session") != user.session_version
        or context.get("mfa") != user.mfa_version
    ):
        raise PermissionDenied
    if not isinstance(decisions, dict) or not set(decisions) <= set(context["paths"]):
        raise ValidationError("Decide only omitted fields from inspected page")
    case, person, listing = reviewer_case(user, case_id)
    current = latest(case, user)
    retry = RightsPortabilityCoverage.objects.filter(
        action__key=key, request=case, actor=user
    ).first()
    if retry is None and (current.pk if current else None) != context["base_id"]:
        raise ValidationError("Coverage version changed")
    with inspection_source(person, listing, case) as source_context:
        saved = _save_page(user, case_id, key, reason, decisions, context, source_context)
    recheck_authority(user, case, person, saved.proof_id)
    return saved


@sensitive_variables()
def _save_page(user, case_id, key, reason, decisions, context, _inspection_source):
    from uuid import UUID

    # Reproduce the original audited page; its source, authority and baseline must still be valid.
    page, _ = _prepare_page(
        user,
        case_id,
        context["version"],
        context["review"],
        UUID(context["key"]),
        context["purpose"],
        context["dataset"],
        context["row_index"],
        context["field_page"],
        baseline_id=context["base_id"],
        use_latest=False,
        _inspection_source=_inspection_source,
    )
    # With no original baseline, replay reconstructs an empty draft, not the newly saved latest row.
    base = RightsPortabilityCoverage.objects.filter(pk=context["base_id"]).first()
    if base and (
        base.version != context["base_version"] or base.coverage_digest != context["base_digest"]
    ):
        raise ValidationError("Coverage baseline changed")
    if (
        page["row"] != context["row"]
        or [item["path"] for item in page["fields"]] != context["paths"]
    ):
        raise ValidationError("Coverage page changed")
    body = (
        unseal(base.encrypted_coverage)
        if base
        else {"omissions": {name: {} for name in SECTIONS}, "image_omissions": {}}
    )
    omissions = deepcopy(body["omissions"])
    dataset, reference = context["dataset"], context["row"]
    combined = deepcopy(page["row_decisions"])
    for path in context["paths"]:
        combined.pop(path, None)
    combined.update(deepcopy(decisions))
    if combined:
        omissions[dataset][reference] = {"fields": combined}
    else:
        omissions[dataset].pop(reference, None)
    return save_coverage(
        user,
        case_id,
        context["version"],
        context["review"],
        key,
        context["base_version"],
        reason,
        omissions,
        deepcopy(body["image_omissions"]),
        allow_partial=True,
        _inspection_source=_inspection_source,
    )
