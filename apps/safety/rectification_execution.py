"""Prior communication of independently approved corrections; execution remains separate."""

import json
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal
from .models import (
    RightsAction,
    RightsRectificationNotification,
    RightsRectificationProposalRead,
    RightsRectificationReview,
)
from .rectification_review import current, permission
from .rights import fingerprint
from .rights_responses import issue
from .rights_scope import locked_case, permitted


@transaction.atomic
@sensitive_variables()
def notify(user, case_id, proposal_id, key, version, reason):
    permission(user)
    if not user.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    case, _, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    signature = fingerprint(
        json.dumps({"proposal": proposal_id, "version": version, "reason": reason}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "rectify_notify"
            and previous.payload_digest == signature
        ):
            return RightsRectificationNotification.objects.get(action=previous)
        raise ValidationError("Conflicting communication key / Clave incompatible")
    case, proposal, proof, changes = current(user, case_id, proposal_id, version)
    review = RightsRectificationReview.objects.select_for_update().filter(proposal=proposal).first()
    digest = fingerprint(json.dumps(changes, sort_keys=True))
    if (
        not review
        or review.outcome != "approved"
        or review.action.actor_id != user.pk
        or review.changes_digest != digest
        or proof.created_at <= review.created_at
        or not 20 <= len(reason.strip()) <= 2000
        or RightsRectificationNotification.objects.filter(review=review).exists()
        or not RightsRectificationProposalRead.objects.filter(
            proposal=proposal, actor=user, proof=proof, case_version=version, changes_digest=digest
        ).exists()
    ):
        raise ValidationError(
            "Read approved changes with fresh proof before communication / Consulta los cambios aprobados con nueva comprobación antes de comunicar"
        )
    text = (
        "Se ha revisado de forma independiente una propuesta de rectificación. "
        "Todavía no se han aplicado cambios. La ejecución requiere recepción de esta comunicación "
        "y una nueva comprobación del ámbito. Simulación de desarrollo; identidad no comprobada. / "
        "A correction proposal has been independently reviewed. No changes have been applied yet. "
        "Execution requires receipt of this communication and a fresh scope check. "
        "Development simulation; identity not verified."
    )
    try:
        with transaction.atomic():
            response = issue(
                user,
                case.pk,
                uuid.uuid4(),
                case.version,
                case.response_version,
                "progress",
                reason,
                text,
                True,
            )
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_notify",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = RightsRectificationNotification.objects.create(
                review=review,
                action=action,
                response=response,
                proof=proof,
                source_digest=proposal.source_digest,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting communication / Comunicación incompatible") from error
    case.refresh_from_db()
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result
