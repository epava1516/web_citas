"""Explicit audited reassessment of the same still-current original decision."""

from django.core.exceptions import PermissionDenied, ValidationError

from .complaint_messages import complete_read
from .complaint_resolutions import source_permission, source_version
from .models import ComplaintAccess, ReportAccess


def validate(user, complaint, decision, decision_id, reviewed_version):
    if not user.has_perm("safety.resolve_complaint") or not source_permission(user, complaint):
        raise PermissionDenied("Independent source reassessment permission required")
    if (
        not decision
        or decision_id != decision.pk
        or complaint.status != "reviewing"
        or complaint.assigned_to_id != user.pk
        or source_version(complaint) != reviewed_version
        or complaint.decision_case_version == reviewed_version
        or not complete_read(user, complaint, reviewed_version)
    ):
        raise ValidationError(
            "Inspect changed assigned source first / Consulta la fuente asignada cambiada"
        )
    if complaint.decision_id:
        report = decision.report
        latest = (
            report.actions.filter(operation__in=["restrict", "dismiss", "uphold", "lift"])
            .order_by("-created_at", "-pk")
            .first()
        )
        if (
            not latest
            or latest.pk != decision.pk
            or report.status not in {"restricted", "upheld", "dismissed", "lifted"}
            or not ReportAccess.objects.filter(
                report=report, actor=user, case_version=reviewed_version, action_before__isnull=True
            ).exists()
        ):
            raise ValidationError(
                "Original decision superseded or unread / Decisión original sustituida o sin consultar"
            )
    else:
        revision = decision.revision
        listing = revision.listing
        latest = revision.decisions.order_by("-created_at", "-pk").first()
        if (
            not latest
            or latest.pk != decision.pk
            or revision.status not in {"approved", "rejected"}
            or revision.manager_version != listing.person.manager_version
            or (revision.status == "approved" and listing.approved_revision_id != revision.pk)
        ):
            raise ValidationError("Original decision superseded / Decisión original sustituida")
        required = set(revision.photos.filter(removed_at__isnull=True).values_list("pk", flat=True))
        read = set(
            ComplaintAccess.objects.filter(
                complaint=complaint,
                actor=user,
                case_version=complaint.version,
                source_version=reviewed_version,
                kind="image",
            ).values_list("photo_id", flat=True)
        )
        if not required.issubset(read):
            raise ValidationError(
                "Inspect all current images / Consulta todas las imágenes vigentes"
            )
