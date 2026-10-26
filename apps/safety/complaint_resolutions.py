"""Independent complaint resolutions; source changes and receipt commit together."""

import json
import re
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.listings.submissions import validate_submission

from .complaint_authority import current_actor
from .complaint_scope import locked, permitted
from .crypto import digest, seal, unseal
from .models import (
    ComplaintAccess,
    ComplaintAction,
    ComplaintNotice,
    ComplaintResolution,
    ReportAccess,
    ReportAction,
)


def source_version(complaint):
    if complaint.decision_id:
        return complaint.decision.report.version
    if complaint.listing_decision_id:
        return complaint.listing_decision.revision.edit_version
    return None


def source_permission(user, complaint):
    permission = "safety.review_report" if complaint.decision_id else "listings.review_listing"
    return bool(
        (complaint.decision_id or complaint.listing_decision_id) and user.has_perm(permission)
    )


@transaction.atomic
@sensitive_variables()
def resolve(
    user, complaint_id, key, version, source_version, outcome, reason, response, redaction_confirmed
):
    session_version, mfa_version = user.session_version, user.mfa_version
    permissions = ("safety.resolve_complaint",)
    user = current_actor(user, session_version, mfa_version, permissions=permissions)
    complaint, source = locked(complaint_id)
    user = current_actor(user, session_version, mfa_version, permissions=permissions)
    unidentified = not complaint.decision_id and not complaint.listing_decision_id
    if not permitted(user, complaint) or (
        not unidentified and not source_permission(user, complaint)
    ):
        raise PermissionDenied("Source permission and independent review required")
    payload = {
        "version": version,
        "source_version": source_version,
        "outcome": outcome,
        "reason": reason,
        "response": response,
        "redaction_confirmed": redaction_confirmed,
    }
    signature = digest(json.dumps(payload, sort_keys=True))
    previous = ComplaintAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.complaint_id == complaint.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
            and previous.operation == "resolve"
        ):
            return complaint
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if (
        complaint.version != version
        or complaint.status != "reviewing"
        or complaint.assigned_to_id != user.pk
        or (unidentified and outcome != "unidentified")
        or (not unidentified and (not source or outcome not in {"upheld", "reconsidered"}))
    ):
        raise ValidationError("Case changed or not assigned / Caso cambiado o no asignado")
    if unidentified:
        question = (
            complaint.actions.filter(operation="clarify", clarification_prompt="reference_unknown")
            .order_by("-pk")
            .first()
        )
        if (
            source_version is not None
            or not question
            or not complaint.messages.filter(created_at__gt=question.created_at).exists()
        ):
            raise ValidationError(
                "Read clarification after reference question first / Revisa la aclaración posterior a la pregunta"
            )
    else:
        current_source = (
            source.report.version if complaint.decision_id else source.revision.edit_version
        )
        if current_source != source_version or complaint.decision_case_version != source_version:
            raise ValidationError(
                "Source changed; reassessment required / Origen cambiado; requiere nueva evaluación"
            )
    from .complaint_messages import complete_read

    if not complete_read(user, complaint, source_version):
        raise ValidationError(
            "Inspect current linked evidence first / Consulta la evidencia enlazada actual"
        )
    if (
        not 20 <= len(reason.strip()) <= 2000
        or not 50 <= len(response.strip()) <= 2000
        or not redaction_confirmed
    ):
        raise ValidationError(
            "Motivated redacted response required / Respuesta motivada y minimizada obligatoria"
        )
    # Technical checks supplement human redaction; they cannot establish privacy by themselves.
    if re.search(r"https?://|www\.|[\w.+-]+@[\w.-]+|(?:\d[\s().+-]*){7}", response, re.I):
        raise ValidationError(
            "Remove links and contact identifiers / Elimina enlaces e identificadores de contacto"
        )
    if complaint.decision_id:
        private = unseal(source.report.encrypted_payload)
        if any(
            value and len(value.strip()) >= 3 and value.casefold() in response.casefold()
            for value in [private.get("name", ""), private.get("email", "")]
        ):
            raise ValidationError(
                "Remove notifier information / Elimina información del notificante"
            )
        resolve_report(user, complaint, source, outcome, reason)
    elif complaint.listing_decision_id:
        required_photos = set(
            source.revision.photos.filter(removed_at__isnull=True).values_list("pk", flat=True)
        )
        inspected_photos = set(
            ComplaintAccess.objects.filter(
                complaint=complaint,
                actor=user,
                case_version=version,
                source_version=source_version,
                kind="image",
            ).values_list("photo_id", flat=True)
        )
        if not required_photos.issubset(inspected_photos):
            raise ValidationError(
                "Inspect all current revision images / Consulta todas las imágenes vigentes de revisión"
            )
        resolve_listing(source, outcome)
    try:
        with transaction.atomic():
            action = ComplaintAction.objects.create(
                key=key,
                complaint=complaint,
                actor=user,
                expected_version=version,
                operation="resolve",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting replay / Reintento incompatible") from error
    resolution = ComplaintResolution.objects.create(
        complaint=complaint,
        action=action,
        outcome=outcome,
        encrypted_response=seal({"response": response}),
    )
    email = unseal(complaint.encrypted_payload).get("email")
    if email:
        ComplaintNotice.objects.create(
            resolution=resolution,
            encrypted_payload=seal(
                {
                    "recipient": email,
                    "subject": "Respuesta a reclamación / Review response",
                    "body": "Hay una respuesta disponible. Consulta tu enlace privado de seguimiento. / A response is available. Consult your private receipt link.",
                }
            ),
        )
    complaint.status = "resolved"
    complaint.version += 1
    complaint.save(update_fields=["status", "version"])
    return complaint


def resolve_report(user, complaint, source, outcome, reason):
    from .decisions import act
    from .notices import enqueue_outcome

    report = source.report
    latest = (
        report.actions.filter(operation__in=["restrict", "dismiss", "uphold", "lift"])
        .order_by("-created_at", "-pk")
        .first()
    )
    if (
        not latest
        or latest.pk != source.pk
        or not ReportAccess.objects.filter(
            report=report, actor=user, case_version=report.version, action_before__isnull=True
        ).exists()
    ):
        raise ValidationError(
            "Inspect latest original decision first / Consulta la última decisión original"
        )
    if report.status in {"restricted", "upheld"}:
        operation = "uphold" if outcome == "upheld" else "lift"
        act(
            user,
            report.pk,
            uuid.uuid4(),
            report.version,
            operation,
            reason,
            manager_version=report.listing.person.manager_version,
            revision_id=report.listing.approved_revision_id,
        )
    elif report.status in {"dismissed", "lifted"}:
        if outcome == "reconsidered":
            action = ReportAction.objects.create(
                key=uuid.uuid4(),
                report=report,
                actor=user,
                expected_version=report.version,
                operation="reopen",
                payload_digest=digest(f"complaint:{complaint.pk}:{complaint.version}"),
                encrypted_reason=seal({"reason": reason}),
            )
            report.status = "received"
            report.assigned_to = None
            report.version += 1
            report.save(update_fields=["status", "assigned_to", "version"])
            enqueue_outcome(report, action)
    else:
        raise ValidationError("Source decision changed / Decisión de origen cambiada")


def resolve_listing(source, outcome):
    revision = source.revision
    listing = revision.listing
    person = listing.person
    latest = revision.decisions.order_by("-created_at", "-pk").first()
    if (
        not latest
        or latest.pk != source.pk
        or revision.status not in {"approved", "rejected"}
        or revision.manager_version != person.manager_version
        or (revision.status == "approved" and listing.approved_revision_id != revision.pk)
    ):
        raise ValidationError("Revision decision changed / Decisión de revisión cambiada")
    if outcome == "upheld":
        return
    if (
        not hasattr(revision, "submission")
        or (
            revision.status == "rejected"
            and revision.submission.approved_base_id != listing.approved_revision_id
        )
        or listing.revisions.filter(status__in=["draft", "processing", "pending"]).count() >= 3
    ):
        raise ValidationError("Current review required / Se requiere revisión vigente")
    validate_submission(revision, person)
    was_approved = revision.status == "approved"
    if was_approved:
        listing.approved_revision_id = revision.submission.approved_base_id
    revision.status = "pending"
    revision.edit_version += 1
    revision.photos.update(approved=False)
    revision.save(update_fields=["status", "edit_version", "updated_at"])
    if was_approved or not listing.approved_revision_id:
        listing.status = "paused" if listing.approved_revision_id else "pending"
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(
            update_fields=["approved_revision", "status", "available_until", "lifecycle_version"]
        )
