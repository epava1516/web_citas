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
from .rights_portability_review import authorize, validate_approved_assessment
from .rights_portability_selection import project_selected
from .rights_portability_selection_store import validate_selection_evidence
from .rights_responses import complete_response_read
from .rights_verification import authorized_proof, complete_read


@transaction.atomic
@sensitive_variables()
def record(user, case_id, version, selection_id, key, purpose, operation="inspect", outcome=""):
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
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
    source = source_copy(person, listing, case)
    source_digest = fingerprint(canonical(source))
    review = row.assessment_review
    previous = RightsAction.objects.filter(key=key).first()
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
        )
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
            try:
                assessment = unseal(review.assessment.encrypted_assessment)
            except (InvalidToken, ValueError, TypeError) as error:
                raise ValidationError("Portability assessment unavailable") from error
            assessment = validate_approved_assessment(
                review, review.assessment, case, proof, source_digest, assessment
            )
            binding = validate_selection_evidence(row, review, case)
            if binding.get("images"):
                from .rights_portability_images import audited_images

                audited_images(row.actor, case, person, source, assessment, binding["images"])
                if operation == "review":
                    from .rights_portability_image_read import required_reads

                    required_reads(row, case, proof, binding["images"], actor.pk, ids=image_reads)
            projected = project_selected(
                source,
                assessment,
                binding["selection"],
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
                fields.update(read=read, outcome=outcome, image_reads=image_reads)
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
                or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
            ):
                raise ValidationError("Selection inspection source changed")
            if operation == "inspect" and "field_evidence" in binding:
                projected["field_evidence"] = binding["field_evidence"]
            if operation == "inspect" and "images" in binding:
                projected["images"] = binding["images"]
            return result, projected if operation == "inspect" else None
    except IntegrityError as error:
        raise ValidationError("Conflicting selection inspection key") from error


# Keep the established inspection service interface.
def inspect(user, case_id, version, selection_id, key, purpose):
    return record(user, case_id, version, selection_id, key, purpose)


@sensitive_variables()
def validate_evidence(evidence, row, case, proof):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Selection review evidence requires enclosing transaction")
    is_review = isinstance(evidence, RightsPortabilitySelectionReview)
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
        "body": fingerprint(row.encrypted_selection),
        "session": evidence.original_session_version,
        "mfa": evidence.original_mfa_version,
        "read": evidence.read_id if is_review else None,
        "outcome": evidence.outcome if is_review else "",
    }
    if is_review and evidence.image_reads:
        signature_input["image_reads"] = evidence.image_reads
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
