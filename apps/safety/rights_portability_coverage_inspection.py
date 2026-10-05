"""Independent audited coverage pages, including omitted values; no approval."""

from itertools import islice
from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverage, RightsPortabilityCoverageRead
from .rights import fingerprint
from .rights_copy_inspection import SECTIONS
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_portability_catalog import FIELD_PAGE_SIZE, scalar_fields
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_pages import baseline_body
from .rights_portability_review import authorize
from .rights_portability_selection import row_reference
from .rights_portability_selection_review import record, validate_approved_selection
from .rights_verification import authorized_proof


@transaction.atomic
@sensitive_variables()
def inspect_page(
    user,
    case_id,
    version,
    coverage_id,
    key,
    purpose,
    dataset,
    row_index=0,
    field_page=1,
    *,
    binary=False,
):
    if (
        type(binary) is not bool
        or (binary and (dataset != "revisions" or row_index != 0))
        or not isinstance(dataset, str)
        or dataset not in SECTIONS
        or type(row_index) is not int
        or row_index < 0
        or type(field_page) is not int
        or field_page < 1
        or not isinstance(purpose, str)
        or not 20 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError("Invalid independent coverage page")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    coverage = (
        RightsPortabilityCoverage.objects.select_for_update(of=("self",))
        .select_related(
            "action",
            "selection_review__selection",
            "selection_review__read__action",
            "selection_review__action",
        )
        .filter(pk=coverage_id, request=case)
        .first()
    )
    if coverage is None or coverage.actor_id == actor.pk:
        raise PermissionDenied("Independent coverage reviewer required")
    # Audited independent selection inspection enforces current read, scope, authority and versions.
    record(
        user,
        case_id,
        version,
        coverage.selection_review.selection_id,
        uuid5(key, f"coverage-inspection:{dataset}:{row_index}:{field_page}:{binary}"),
        purpose,
    )
    proof = authorized_proof(case, person, case.kind)
    decision = coverage.selection_review
    selection = decision.selection
    validate_approved_selection(decision, selection, case, proof)
    source = source_copy(person, listing, case)
    if fingerprint(canonical(source)) != coverage.source_digest:
        raise ValidationError("Coverage inspection source changed")
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "coverage": coverage.pk,
                "coverage_digest": coverage.coverage_digest,
                "ciphertext": fingerprint(coverage.encrypted_coverage),
                "proof": str(proof.pk),
                "selection": selection.pk,
                "source": coverage.source_digest,
                "dataset": dataset,
                "row": row_index,
                "page": field_page,
                "binary": binary,
                "purpose": purpose,
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
                    actor=actor,
                    operation="coverage_inspect",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": purpose}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage inspection key") from error
    if (
        action.request_id,
        action.actor_id,
        action.operation,
        action.expected_version,
        action.payload_digest,
    ) != (case.pk, actor.pk, "coverage_inspect", version, signature):
        raise ValidationError("Conflicting coverage inspection key")
    try:
        if unseal(action.encrypted_reason) != {"reason": purpose}:
            raise ValidationError("Coverage inspection reason changed")
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage inspection reason unavailable") from error
    author = User.objects.get(pk=coverage.actor_id)
    body = baseline_body(coverage, case, author, selection, decision)
    facts = unseal(selection.encrypted_selection)
    assessment = unseal(selection.assessment_review.assessment.encrypted_assessment)
    summary = compile_coverage(
        source,
        assessment,
        facts["selection"],
        body["omissions"],
        facts.get("images", []),
        body["image_omissions"],
        field_evidence=facts.get("field_evidence"),
        allow_partial=True,
    )
    if binary:
        rows = [image for revision in source["revisions"] for image in revision["images"]]
        start = (field_page - 1) * 20
        fields = [dict(item) for item in rows[start : start + 20]]
        if field_page > 1 and not fields:
            raise ValidationError("Coverage binary page unavailable")
        included = {item["photo"]: item["conditions"] for item in facts.get("images", [])}
        for item in fields:
            if assessment["revisions"]["status"] == "excluded":
                item.update(status="excluded", conditions=assessment["revisions"])
            elif item["photo"] in included:
                item.update(status="included", conditions=included[item["photo"]])
            else:
                conditions = body["image_omissions"].get(item["photo"])
                item.update(status="excluded" if conditions else "pending", conditions=conditions)
        reference, more = None, start + 20 < len(rows)
    else:
        rows = SECTIONS[dataset](source)
        if not rows:
            if row_index or field_page != 1:
                raise ValidationError("Coverage inspection page unavailable")
            fields, reference, more = [], None, False
        else:
            if row_index >= len(rows):
                raise ValidationError("Coverage inspection row unavailable")
            row = rows[row_index]
            reference = row_reference(dataset, row_index, row)
            start = (field_page - 1) * FIELD_PAGE_SIZE
            fields = list(islice(scalar_fields(row), start, start + FIELD_PAGE_SIZE + 1))
            if field_page > 1 and not fields:
                raise ValidationError("Coverage inspection page unavailable")
            more, fields = len(fields) > FIELD_PAGE_SIZE, fields[:FIELD_PAGE_SIZE]
            selected = next(
                (
                    set(item["fields"])
                    for item in facts["selection"].get(dataset, [])
                    if item["row"] == reference
                ),
                set(),
            )
            omitted = body["omissions"][dataset].get(reference, {})
            for item in fields:
                if assessment[dataset]["status"] == "excluded":
                    item.update(status="excluded", conditions=assessment[dataset])
                elif item["path"] in selected:
                    item.update(
                        status="included",
                        conditions=facts.get("field_evidence", {})
                        .get(dataset, {})
                        .get(reference, {})
                        .get(item["path"], assessment[dataset]),
                    )
                else:
                    conditions = omitted.get("all", omitted.get("fields", {}).get(item["path"]))
                    item.update(
                        status="excluded" if conditions else "pending", conditions=conditions
                    )
    authorize(user, case)
    if (
        authorized_proof(case, person, case.kind).pk != proof.pk
        or fingerprint(canonical(source_copy(person, listing, case))) != coverage.source_digest
    ):
        raise ValidationError("Coverage inspection authority or source changed")
    result = {
        "dataset": dataset,
        "binary": binary,
        "row": reference,
        "row_index": row_index,
        "row_count": len(rows),
        "field_page": field_page,
        "fields": fields,
        "has_next_fields": more,
        "has_next_row": row_index + 1 < len(rows),
        "summary": {k: v for k, v in summary.items() if k != "projection"},
    }

    page_digest = fingerprint(canonical(result))
    expected = {
        "coverage_id": coverage.pk,
        "proof_id": proof.pk,
        "source_digest": coverage.source_digest,
        "coverage_digest": coverage.coverage_digest,
        "original_session_version": user.session_version,
        "original_mfa_version": user.mfa_version,
        "dataset": dataset,
        "row_index": row_index,
        "field_page": field_page,
        "binary": binary,
        "page_digest": page_digest,
    }
    read = RightsPortabilityCoverageRead.objects.filter(action=action).first()
    if read:
        if any(getattr(read, name) != value for name, value in expected.items()):
            raise ValidationError("Coverage page record changed")
    else:
        try:
            with transaction.atomic():
                RightsPortabilityCoverageRead.objects.create(action=action, **expected)
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage page record") from error
    return action, result
