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


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, proposal_id, key, version, reason):
    from copy import deepcopy

    from apps.listings.models import Rate, Revision
    from apps.mediafiles.models import Photo
    from apps.mediafiles.tasks import process_blob

    from . import (
        rectification_catalog,
        rectification_contacts,
        rectification_details,
        rectification_location,
        rectification_rates,
    )
    from .models import RightsRectificationExecution

    permission(user)
    if not user.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    case, person, listing = locked_case(case_id, lock_listing=True)
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
            and previous.operation == "rectify_execute"
            and previous.payload_digest == signature
        ):
            return RightsRectificationExecution.objects.get(action=previous)
        raise ValidationError("Conflicting execution key / Clave incompatible")
    case, proposal, proof, changes = current(user, case_id, proposal_id, version)
    notification = (
        RightsRectificationNotification.objects.select_for_update()
        .select_related("review__action", "response")
        .filter(review__proposal=proposal)
        .first()
    )
    ack = getattr(notification.response, "receipt_acknowledgement", None) if notification else None
    if (
        not notification
        or notification.review.outcome != "approved"
        or notification.review.action.actor_id != user.pk
        or notification.source_digest != proposal.source_digest
        or notification.review.changes_digest != fingerprint(json.dumps(changes, sort_keys=True))
        or notification.response.response_version != case.response_version
        or not ack
        or ack.channel_digest != case.receipt_digest
        or proof.created_at <= ack.created_at
        or proof.created_at <= notification.created_at
        or not 20 <= len(reason.strip()) <= 2000
        or RightsRectificationExecution.objects.filter(notification=notification).exists()
        or not RightsRectificationProposalRead.objects.filter(
            proposal=proposal,
            actor=user,
            proof=proof,
            case_version=version,
            changes_digest=notification.review.changes_digest,
        ).exists()
        or person.publication_erased_at
    ):
        raise ValidationError(
            "Current received correction and fresh check required / Rectificación recibida vigente y nueva comprobación obligatorias"
        )
    if listing and listing.revisions.filter(status__in=["draft", "processing", "pending"]).exists():
        raise ValidationError(
            "Resolve ongoing revisions first / Resuelve primero las revisiones en curso"
        )
    source = proposal.source_revision
    corrected = None
    before = {"alias": person.alias}
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_execute",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            if source:
                excluded = {
                    "id",
                    "listing",
                    "source_revision",
                    "manager_version",
                    "status",
                    "step",
                    "edit_version",
                    "created_at",
                    "updated_at",
                    "publisher_acceptance",
                    "contact_exposure_accepted",
                }
                values = {
                    field.attname: deepcopy(getattr(source, field.attname))
                    for field in Revision._meta.concrete_fields
                    if field.name not in excluded
                }
                before.update(
                    {
                        field: getattr(source, field)
                        for field in changes
                        if field
                        not in {"alias", "location", "catalog", "rates", "contacts", "details"}
                    }
                )
                values.update(
                    {
                        field: text
                        for field, text in changes.items()
                        if field
                        not in {"alias", "location", "catalog", "rates", "contacts", "details"}
                    }
                )
                if "details" in changes:
                    before["details"] = rectification_details.source(source)
                    values.update(
                        {
                            field: changes["details"][field]
                            for field in rectification_details.SCALARS
                        }
                    )
                if "contacts" in changes:
                    before["contacts"] = rectification_contacts.source(source)
                    before["phone_binding"] = rectification_contacts.binding(person)
                    values.update(changes["contacts"])
                if "rates" in changes:
                    before["rates"] = rectification_rates.source(source)
                if "catalog" in changes:
                    before["catalog"] = rectification_catalog.source(source)
                if "location" in changes:
                    before["location"] = rectification_location.source(source)
                    values.update(
                        {
                            field + "_id": identifier
                            for field, identifier in changes["location"].items()
                        }
                    )
                corrected = Revision.objects.create(
                    listing=listing,
                    source_revision=source,
                    manager_version=person.manager_version,
                    **values,
                )
                for field in Revision._meta.many_to_many:
                    if "catalog" in changes and field.name in {"categories", "services"}:
                        getattr(corrected, field.name).set(changes["catalog"][field.name])
                    elif "details" in changes and field.name == "travel_areas":
                        corrected.travel_areas.set(changes["details"]["travel_areas"])
                    else:
                        getattr(corrected, field.name).set(getattr(source, field.name).all())
                rate_values = changes.get("rates", rectification_rates.source(source))
                for rate in rate_values:
                    Rate.objects.create(revision=corrected, **rate)
                Photo.objects.bulk_create(
                    [
                        Photo(revision=corrected, blob_id=photo.blob_id, position=photo.position)
                        for photo in source.photos.filter(removed_at__isnull=True)
                    ]
                )
                for blob_id in set(
                    str(value)
                    for value in source.photos.filter(removed_at__isnull=True).values_list(
                        "blob_id", flat=True
                    )
                ):
                    transaction.on_commit(
                        lambda blob_id=blob_id: process_blob.delay(blob_id), robust=True
                    )
            if "alias" in changes:
                person.alias = changes["alias"]
            if "contacts" in changes:
                person.phone_claim = rectification_contacts.claim(changes["contacts"], person)
            person.rights_version += 1
            person.save(update_fields=["alias", "rights_version", "phone_claim"])
            if listing:
                if listing.status == "published":
                    listing.status = "paused"
                listing.available_until = None
                listing.lifecycle_version += 1
                listing.save(update_fields=["status", "available_until", "lifecycle_version"])
            result = RightsRectificationExecution.objects.create(
                notification=notification,
                action=action,
                proof=proof,
                corrected_revision=corrected,
                encrypted_previous_values=seal(before),
                resulting_rights_version=person.rights_version,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting execution / Ejecución incompatible") from error
    response = issue(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        case.response_version,
        "progress",
        reason,
        "Se han aplicado cambios al perfil y, cuando existe anuncio, se ha preparado una nueva versión corregida. "
        "La publicación permanece pausada y requiere revisión antes de reanudarse. La solicitud sigue abierta. "
        "Simulación de desarrollo; identidad no comprobada. / Changes have been applied to the profile and, "
        "where a listing exists, a corrected version has been prepared. Publication remains paused and "
        "requires review before resuming. The request remains open. Development simulation; identity not verified.",
        True,
    )
    from .rectification_notices import create as create_manager_notices

    create_manager_notices(result, person)
    result.response = response
    result.save(update_fields=["response"])
    case.refresh_from_db()
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result
