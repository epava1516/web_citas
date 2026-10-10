"""Independent audited selection inspection and decisions; no delivery."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsPortabilitySelection,
    RightsPortabilitySelectionRead,
    RightsPortabilitySelectionReview,
)
from .rights import fingerprint
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_inspection_source import inspection_source, shared_source
from .rights_inspection_source import source_digest as shared_or_computed
from .rights_portability_review import authorize, validate_approved_assessment
from .rights_portability_selection import project_selected
from .rights_portability_selection_pages import complete_pages, project_page, valid_metadata
from .rights_portability_selection_store import validate_selection_evidence
from .rights_responses import complete_response_read
from .rights_verification import authorized_proof, complete_read


@transaction.atomic
@sensitive_variables()
def record(
    user,
    case_id,
    version,
    selection_id,
    key,
    purpose,
    operation="inspect",
    outcome="",
    *,
    _inspection_source=None,
    page=None,
    _require_pages=False,
):
    if type(_require_pages) is not bool or (_require_pages and operation != "review"):
        raise ValidationError("Invalid selection review mode")
    if page is not None and (operation != "inspect" or type(page) is not int or page < 1):
        raise ValidationError("Invalid selection page")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    if operation == "inspect" and _inspection_source is None:
        # One audited source per inspection; its exit compares fresh DB rows inside this
        # transaction, then reviewer/proof are rechecked after that potentially long read.
        with inspection_source(person, listing, case) as context:
            result = record(user, case_id, version, selection_id, key, purpose, operation, outcome,
                            _inspection_source=context, page=page)
        authorize(user, case)
        if authorized_proof(case, person, case.kind).pk != result[0].proof_id:
            raise ValidationError("Selection inspection authority changed before return")
        return result
    if (
        case.kind != "portability"
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
        or not isinstance(purpose, str)
        or not 20 <= len(purpose.strip()) <= 200
        or operation not in {"inspect", "review"}
        or (operation == "inspect" and outcome)
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Inspect current request before selection review")
    row = (
        RightsPortabilitySelection.objects.select_for_update(of=("self",))
        .select_related(
            "action",
            "assessment_review__assessment__action",
            "assessment_review__read__action",
            "assessment_review__action",
        )
        .filter(pk=selection_id, request=case)
        .first()
    )
    if row is None or row.actor_id == actor.pk:
        raise PermissionDenied("Independent selection reviewer required")
    if operation == "review" and (
        RightsPortabilitySelection.objects.filter(request=case)
        .order_by("-created_at", "-pk")
        .first()
        .pk
        != row.pk
    ):
        raise ValidationError("Latest portability selection required")
    proof = authorized_proof(case, person, case.kind)
    if _inspection_source is not None and operation != "inspect":
        raise ValidationError("Shared inspection source cannot authorize a selection decision")
    source = (
        shared_source(_inspection_source, person, listing, case)
        if _inspection_source is not None
        else source_copy(person, listing, case)
    )
    source_digest = shared_or_computed(_inspection_source, person, listing, case, source)
    review = row.assessment_review
    page_metadata, page_body, prepared = {}, None, None
    if page is not None:
        try:
            assessment_body = unseal(review.assessment.encrypted_assessment)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Portability assessment unavailable") from error
        assessment = validate_approved_assessment(
            review, review.assessment, case, proof, source_digest, assessment_body,
        )
        binding = validate_selection_evidence(row, review, case)
        projected = project_selected(source, assessment, binding["selection"],
                                     field_evidence=binding.get("field_evidence"))
        page_body, page_metadata = project_page(projected, binding, page)
        prepared = assessment, binding, projected
    previous = RightsAction.objects.filter(key=key).first()
    page_reads = []
    image_reads = []
    if operation == "review":
        from .models import RightsPortabilityImageRead

        if previous:
            original_decision = RightsPortabilitySelectionReview.objects.filter(
                action=previous
            ).first()
            image_reads = original_decision.image_reads if original_decision else []
        else:
            image_reads = list(
                RightsPortabilityImageRead.objects.filter(
                    selection=row,
                    action__actor=actor,
                    proof=proof,
                    action__expected_version=version,
                    selection_digest=row.selection_digest,
                )
                .order_by("photo_id", "-pk")
                .distinct("photo_id")
                .values_list("pk", flat=True)
            )
    read = None
    if operation == "review":
        reads = RightsPortabilitySelectionRead.objects.select_related("action").filter(
            selection=row,
            action__actor=actor,
            action__expected_version=version,
            proof=proof,
            source_digest=source_digest,
            selection_digest=row.selection_digest,
            original_session_version=user.session_version,
            original_mfa_version=user.mfa_version,
        )
        if _require_pages:
            reads = reads.exclude(page_metadata={})
        if previous:
            reads = reads.filter(
                pk__in=RightsPortabilitySelectionReview.objects.filter(action=previous).values(
                    "read_id"
                )
            )
        read = reads.order_by("-pk").first()
        if read is None:
            raise ValidationError("Inspect this selection before deciding")
        validate_evidence(read, row, case, proof)
        if read.page_metadata:
            original_review = RightsPortabilitySelectionReview.objects.filter(action=previous).first() if previous else None
            page_reads = complete_pages(row, case, proof, actor.pk, user.session_version,
                                        user.mfa_version, ids=original_review.page_reads if original_review else None)
    signature_input = {
        "selection": row.pk,
        "version": version,
        "purpose": purpose,
        "source": source_digest,
        "proof": str(proof.pk),
        "digest": row.selection_digest,
        "body": fingerprint(row.encrypted_selection),
        "session": user.session_version,
        "mfa": user.mfa_version,
        "read": read.pk if read else None,
        "outcome": outcome,
    }
    if image_reads:
        signature_input["image_reads"] = image_reads
    if page_metadata:
        signature_input["selection_page"] = page_metadata
    if page_reads:
        signature_input["page_reads"] = page_reads
    signature = fingerprint(canonical(signature_input))
    if previous and (
        previous.request_id != case.pk
        or previous.actor_id != actor.pk
        or previous.expected_version != version
        or previous.operation != "selection_" + operation
        or previous.payload_digest != signature
    ):
        raise ValidationError("Conflicting selection inspection key")
    try:
        with transaction.atomic():
            action = previous or RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation="selection_" + operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": purpose}),
            )
            if prepared is None:
                try:
                    assessment = unseal(review.assessment.encrypted_assessment)
                except (InvalidToken, ValueError, TypeError) as error:
                    raise ValidationError("Portability assessment unavailable") from error
                assessment = validate_approved_assessment(
                    review, review.assessment, case, proof, source_digest, assessment
                )
                binding = validate_selection_evidence(row, review, case)
            else:
                assessment, binding, projected = prepared
            if binding.get("images"):
                from .rights_portability_images import audited_images

                audited_images(row.actor, case, person, source, assessment, binding["images"])
                if operation == "review":
                    from .rights_portability_image_read import required_reads

                    required_reads(row, case, proof, binding["images"], actor.pk, ids=image_reads)
            if prepared is None:
                projected = project_selected(
                    source, assessment, binding["selection"],
                    field_evidence=binding.get("field_evidence"),
                )
            model = (
                RightsPortabilitySelectionRead
                if operation == "inspect"
                else RightsPortabilitySelectionReview
            )
            fields = dict(
                action=action,
                selection=row,
                proof=proof,
                source_digest=source_digest,
                selection_digest=row.selection_digest,
                original_session_version=user.session_version,
                original_mfa_version=user.mfa_version,
            )
            if operation == "review":
                fields.update(read=read, outcome=outcome, image_reads=image_reads, page_reads=page_reads)
            else:
                fields["page_metadata"] = page_metadata
            if previous:
                result = model.objects.select_related("action").filter(**fields).first()
                if result is None:
                    raise ValidationError("Selection inspection evidence changed")
            else:
                if (
                    operation == "review"
                    and RightsPortabilitySelectionReview.objects.filter(selection=row).exists()
                ):
                    raise ValidationError("Selection already reviewed")
                result = model.objects.create(**fields)
            validate_evidence(result, row, case, proof)
            authorize(user, case)
            if (
                authorized_proof(case, person, case.kind).pk != proof.pk
                or shared_or_computed(_inspection_source, person, listing, case) != source_digest
            ):
                raise ValidationError("Selection inspection source changed")
            if operation == "inspect" and "field_evidence" in binding:
                projected["field_evidence"] = binding["field_evidence"]
            if operation == "inspect" and "images" in binding:
                projected["images"] = binding["images"]
            return result, (page_body if page is not None else projected) if operation == "inspect" else None
    except IntegrityError as error:
        raise ValidationError("Conflicting selection inspection key") from error


# Keep the established inspection service interface.
def inspect(user, case_id, version, selection_id, key, purpose):
    return record(user, case_id, version, selection_id, key, purpose)


@sensitive_variables()
def validate_evidence(evidence, row, case, proof, *, _body_digest=None):
    """``_body_digest`` lets a caller validating many reads of one locked row pass
    ``fingerprint(row.encrypted_selection)`` computed once; it must come from this same row."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Selection review evidence requires enclosing transaction")
    is_review = isinstance(evidence, RightsPortabilitySelectionReview)
    if is_review:
        if not isinstance(evidence.page_reads, list):
            raise ValidationError("Invalid selection page references")
    elif not isinstance(evidence.page_metadata, dict) or (evidence.page_metadata and not valid_metadata(evidence.page_metadata)):
        raise ValidationError("Invalid selection page metadata")
    try:
        reason = unseal(evidence.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Selection review evidence unavailable") from error
    signature_input = {
        "selection": row.pk,
        "version": case.version,
        "purpose": reason,
        "source": row.source_digest,
        "proof": str(proof.pk),
        "digest": row.selection_digest,
        "body": _body_digest if _body_digest is not None else fingerprint(row.encrypted_selection),
        "session": evidence.original_session_version,
        "mfa": evidence.original_mfa_version,
        "read": evidence.read_id if is_review else None,
        "outcome": evidence.outcome if is_review else "",
    }
    if is_review and evidence.image_reads:
        signature_input["image_reads"] = evidence.image_reads
    if is_review and evidence.page_reads:
        signature_input["page_reads"] = evidence.page_reads
    elif not is_review and evidence.page_metadata:
        signature_input["selection_page"] = evidence.page_metadata
    signature = fingerprint(canonical(signature_input))
    if (
        evidence.selection_id != row.pk
        or evidence.proof_id != proof.pk
        or evidence.source_digest != row.source_digest
        or evidence.selection_digest != row.selection_digest
        or evidence.action.request_id != case.pk
        or evidence.action.expected_version != case.version
        or evidence.action.actor_id == row.actor_id
        or evidence.action.operation != ("selection_review" if is_review else "selection_inspect")
        or evidence.action.payload_digest != signature
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
        or (is_review and evidence.outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Selection review evidence changed")
    if is_review:
        linked = RightsPortabilitySelectionRead.objects.select_related("action").get(
            pk=evidence.read_id
        )
        if linked.action.actor_id != evidence.action.actor_id:
            raise ValidationError("Selection review reader changed")
        validate_evidence(linked, row, case, proof)
        if linked.page_metadata:
            if linked.pk not in evidence.page_reads:
                raise ValidationError("Selection review pages incomplete")
            complete_pages(row, case, proof, evidence.action.actor_id,
                           evidence.original_session_version, evidence.original_mfa_version,
                           ids=evidence.page_reads)
        elif evidence.page_reads:
            raise ValidationError("Selection review page mode changed")


@sensitive_variables()
def validate_approved_selection(decision, row, case, proof):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Approved selection requires enclosing transaction")
    latest = (
        RightsPortabilitySelection.objects.filter(request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    if latest is None or latest.pk != row.pk:
        raise ValidationError("Latest portability selection required")
    if decision.selection_id != row.pk or decision.outcome != "approved":
        raise ValidationError("Approved portability selection required")
    validate_evidence(decision, row, case, proof)
    from .rights_portability_image_read import required_reads

    selected = validate_selection_evidence(row, row.assessment_review, case)
    required_reads(
        row,
        case,
        proof,
        selected.get("images", []),
        decision.action.actor_id,
        ids=decision.image_reads,
    )
