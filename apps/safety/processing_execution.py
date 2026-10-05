"""Execute supported reviewed purposes without deleting data or closing the right."""

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .erasure_inventory import canonical
from .models import (
    PrivacyPublicationHold,
    ProcessingExecution,
    ProcessingPlanReview,
    PurposeRestriction,
    RightsAction,
)
from .processing_review import authorize, contents, current
from .rights import fingerprint
from .rights_scope import locked_case

SUPPORTED = {"account_preferences", "publication"}


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, plan_id, key, version, purposes, reason, confirmed):
    case, person, listing = locked_case(
        case_id, lock_listing=True, allow_version_change=True, allow_erased_account=True
    )
    fresh = authorize(user, case, review_permission=False)
    if (
        not isinstance(purposes, list)
        or not purposes
        or any(not isinstance(p, str) for p in purposes)
        or len(purposes) != len(set(purposes))
        or not set(purposes) <= SUPPORTED
        or confirmed is not True
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError(
            "Confirm supported selected purposes / Confirma finalidades seleccionadas implementadas"
        )
    signature = fingerprint(
        canonical(
            {
                "plan": str(plan_id),
                "version": version,
                "purposes": sorted(purposes),
                "reason": reason,
                "confirmed": confirmed,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "processing_execute"
            and previous.payload_digest == signature
        ):
            return ProcessingExecution.objects.get(action=previous)
        raise ValidationError("Conflicting replay / Reintento incompatible")
    fresh, case, plan, proof, manifest = current(
        user, case_id, plan_id, version, review_permission=False
    )
    if case.assigned_to_id != fresh.pk:
        raise PermissionDenied("Assigned executor required")
    review = ProcessingPlanReview.objects.select_for_update().filter(plan=plan).first()
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if "publication" in purposes and (not person or case.account_subject_id):
        raise ValidationError(
            "Publication requires profile scope / Publicación exige ámbito de perfil"
        )
    if "account_preferences" in purposes and not subject_id:
        raise ValidationError("Subject account unidentified / Cuenta del sujeto sin identificar")
    subject = (
        User.objects.select_for_update(no_key=True).get(pk=subject_id)
        if "account_preferences" in purposes
        else None
    )
    # Authority/source must be read after the approval and target-account waits.
    fresh, case, plan, proof, manifest = current(
        user, case_id, plan_id, version, review_permission=False
    )
    if (
        not review
        or review.outcome != "approved"
        or review.proof_id != proof.pk
        or review.source_digest != plan.source_digest
        or review.plan_digest != fingerprint(plan.encrypted_plan)
        or review.action.actor_id == plan.action.actor_id
    ):
        raise ValidationError(
            "Current independent approval required / Aprobación independiente vigente obligatoria"
        )
    body = contents(plan, manifest)
    decisions = {row["purpose"]: row for row in body["decisions"]}
    if any(
        p not in decisions or decisions[p]["operation"] not in {"restrict", "cease"}
        for p in purposes
    ):
        raise ValidationError(
            "Selected purposes have no approved restriction / Finalidades seleccionadas sin restricción aprobada"
        )
    if PurposeRestriction.objects.filter(execution__review=review, purpose__in=purposes).exists():
        raise ValidationError("Purpose already executed / Finalidad ya ejecutada")
    if (
        "publication" in purposes
        and ProcessingExecution.objects.filter(
            review=review, publication_hold__isnull=False
        ).exists()
    ):
        raise ValidationError("Purpose already executed / Finalidad ya ejecutada")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="processing_execute",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = ProcessingExecution.objects.create(
                action=action,
                review=review,
                proof=proof,
                person=person if not case.account_subject_id else None,
                account_subject_id=case.account_subject_id,
                source_digest=plan.source_digest,
                encrypted_result=seal(
                    {
                        "schema": "processing-execution-v1",
                        "blocked": sorted(purposes),
                        "partial": True,
                        "data_deleted": False,
                        "remaining_purposes": sorted(set(decisions) - set(purposes)),
                    }
                ),
            )
            for purpose in purposes:
                decision = decisions[purpose]
                if purpose == "publication":
                    hold = PrivacyPublicationHold.objects.create(
                        action=action,
                        proof=proof,
                        person=person,
                        subject_snapshot=str(person.subject_id or ""),
                        manager_version=person.manager_version,
                        ground="purpose_" + decision["operation"],
                        purpose_review_on=date.fromisoformat(decision["review_on"]),
                        initial_purpose_review_on=date.fromisoformat(decision["review_on"]),
                        previous_listing_status=listing.status if listing else "",
                        previous_lifecycle_version=listing.lifecycle_version if listing else None,
                    )
                    result.publication_hold = hold
                    result.save(update_fields=["publication_hold"])
                    if listing:
                        if listing.status == "published":
                            listing.status = "paused"
                        listing.available_until = None
                        listing.lifecycle_version += 1
                        listing.save(
                            update_fields=["status", "available_until", "lifecycle_version"]
                        )
                    continue
                PurposeRestriction.objects.create(
                    execution=result,
                    subject=subject,
                    purpose=purpose,
                    mode=decision["operation"],
                    review_on=date.fromisoformat(decision["review_on"]),
                    initial_review_on=date.fromisoformat(decision["review_on"]),
                )
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            authorize(user, case, review_permission=False)
            return result
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting execution key / Clave de ejecución incompatible"
        ) from error
