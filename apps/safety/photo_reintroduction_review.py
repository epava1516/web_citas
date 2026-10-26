"""Scoped audit and independent decisions; no automatic publication or account ban."""

import json

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User
from apps.listings.history import is_rectification_history
from apps.listings.models import Revision
from apps.mediafiles.models import Blob, Photo

from .crypto import seal, unseal
from .models import (
    RightsPhotoReintroduction,
    RightsPhotoReintroductionDecision,
    RightsPhotoReintroductionRead,
)
from .photo_dispositions import active_withdrawals
from .rights import fingerprint
from .rights_scope import locked_profile_case as locked_case
from .rights_scope import permitted


def permission(user):
    current = User.objects.filter(pk=user.pk).first()
    if (
        current is None
        or not current.is_active
        or current.account_erased_at
        or not current.mfa_enabled
        or current.session_version != user.session_version
        or current.mfa_version != user.mfa_version
        or not current.has_perm("safety.review_photo_reintroduction")
    ):
        raise PermissionDenied
    return current


def source(candidate):
    photo = Photo.objects.select_related("revision__listing__person").get(pk=candidate.photo_id)
    disposition = candidate.disposition
    person = photo.revision.listing.person
    blobs = Blob.objects.filter(pk__in=[candidate.uploaded_blob_id, disposition.blob_id])
    execution = disposition.execution
    resources = list(
        blobs.order_by("pk").values(
            "pk", "sha256", "status", "original", "derivative", "signature", "width", "height"
        )
    )
    return fingerprint(
        json.dumps(
            {
                "candidate": candidate.pk,
                "method": candidate.method,
                "score": candidate.score,
                "photo": photo.pk,
                "blob": photo.blob_id,
                "removed": photo.removed_at,
                "revision": photo.revision_id,
                "manager": person.manager_version,
                "rights": person.rights_version,
                "execution": execution.pk,
                "proof": execution.proof_id,
                "proof_status": execution.proof.status,
                "review_outcome": execution.notification.review.outcome,
                "disposition": disposition.pk,
                "outcome": disposition.outcome,
                "active": active_withdrawals(person.pk).filter(pk=disposition.pk).exists(),
                "resources": resources,
            },
            sort_keys=True,
            default=str,
        )
    )


def active(revision):
    return RightsPhotoReintroduction.objects.filter(
        photo__revision=revision,
        photo__removed_at__isnull=True,
        uploaded_blob_id=F("photo__blob_id"),
        disposition__in=active_withdrawals(revision.listing.person_id),
    ).select_related("disposition")


def publication_pending(revision):
    for candidate in active(revision):
        decision = candidate.decisions.order_by("-review_version").first()
        if (
            not decision
            or decision.outcome == "maintain"
            or decision.source_digest != source(candidate)
        ):
            return True
    return False


def locked(user, candidate_id):
    permission(user)
    initial = RightsPhotoReintroduction.objects.select_related(
        "disposition__execution__notification__review__proposal__action",
        "disposition__execution__action",
        "disposition__execution__proof",
    ).get(pk=candidate_id)
    execution = initial.disposition.execution
    proposal = execution.notification.review.proposal
    case, person, _ = locked_case(
        proposal.action.request_id, lock_listing=True, allow_version_change=True
    )
    # Authority can change while waiting for scope locks; discard the pre-lock snapshot.
    execution = (
        type(execution)
        .objects.select_related("proof", "notification__review__proposal__action", "action")
        .get(pk=execution.pk)
    )
    proposal = execution.notification.review.proposal
    if (
        not permitted(user, case)
        or user.pk in [proposal.action.actor_id, execution.action.actor_id]
        or execution.proof.status != "passed"
        or (settings.PRODUCTION and execution.proof.procedure.startswith("simulator"))
    ):
        raise PermissionDenied
    candidate = RightsPhotoReintroduction.objects.select_for_update().get(pk=candidate_id)
    revision = Revision.objects.select_for_update().get(pk=candidate.photo.revision_id)
    blobs = list(
        Blob.objects.select_for_update()
        .filter(pk__in=[candidate.uploaded_blob_id, candidate.disposition.blob_id])
        .order_by("pk")
    )
    # Discard cached operator permissions after every scope/media lock wait.
    current = permission(user)
    if not permitted(current, case):
        raise PermissionDenied
    photo = Photo.objects.get(pk=candidate.photo_id)
    if (
        not person
        or revision.listing.person_id != person.pk
        or revision.manager_version != person.manager_version
        or photo.removed_at
        or photo.blob_id != candidate.uploaded_blob_id
        or revision.status == "rights-stage"
        or hasattr(photo, "rectification_upload")
        or is_rectification_history(revision)
        or any(blob.status != "ready" or not blob.derivative for blob in blobs)
        or not active_withdrawals(person.pk).filter(pk=candidate.disposition_id).exists()
    ):
        raise ValidationError("Image review changed / Revisión de imagen cambiada")
    return candidate


@transaction.atomic
@sensitive_variables()
def inspect(user, candidate_id, key, version, purpose):
    candidate = locked(user, candidate_id)
    digest = source(candidate)
    previous = RightsPhotoReintroductionRead.objects.filter(key=key).first()
    if previous:
        if (
            previous.candidate_id == candidate.pk
            and previous.actor_id == user.pk
            and previous.review_version == version
            and previous.source_digest == digest
            and previous.purpose == purpose
            and candidate.review_version == version
        ):
            return previous
        raise ValidationError("Conflicting audit key / Clave de consulta incompatible")
    if candidate.review_version != version or not 20 <= len(purpose.strip()) <= 200:
        raise ValidationError(
            "Current review and purpose required / Revisión vigente y motivo obligatorios"
        )
    return RightsPhotoReintroductionRead.objects.create(
        key=key,
        candidate=candidate,
        actor=user,
        review_version=version,
        source_digest=digest,
        purpose=purpose,
    )


@transaction.atomic
@sensitive_variables()
def decide(user, candidate_id, read_id, key, version, outcome, reason, reference):
    candidate = locked(user, candidate_id)
    digest = source(candidate)
    previous = RightsPhotoReintroductionDecision.objects.filter(key=key).first()
    values = {"reason": reason, "reference": reference}
    if previous:
        if (
            previous.candidate_id == candidate.pk
            and previous.read_id == read_id
            and previous.read.actor_id == user.pk
            and previous.review_version == version
            and previous.outcome == outcome
            and previous.source_digest == digest
            and unseal(previous.encrypted_reason) == values
        ):
            return previous
        raise ValidationError("Conflicting decision key / Clave de decisión incompatible")
    read = RightsPhotoReintroductionRead.objects.filter(
        pk=read_id,
        candidate=candidate,
        actor=user,
        review_version=version,
        source_digest=digest,
    ).first()
    if (
        not read
        or candidate.review_version != version
        or outcome not in {"maintain", "false_positive", "authorize"}
        or (outcome == "false_positive" and candidate.method == "sha256")
        or not 20 <= len(reason.strip()) <= 2000
        or not 3 <= len(reference.strip()) <= 200
    ):
        raise ValidationError(
            "Audited current independent decision required / Decisión independiente vigente y consultada obligatoria"
        )
    result = RightsPhotoReintroductionDecision.objects.create(
        key=key,
        candidate=candidate,
        read=read,
        review_version=version,
        source_digest=digest,
        outcome=outcome,
        encrypted_reason=seal(values),
    )
    candidate.review_version += 1
    candidate.save(update_fields=["review_version"])
    return result
