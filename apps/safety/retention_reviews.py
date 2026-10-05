"""Per-purpose follow-up calendar; it cannot extend legal retention or execute erasure."""

from datetime import date, timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .models import ErasurePlan, RetentionReview, RetentionReviewEvent
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import complete_read


def schedule(plan, decisions):
    """Called inside plan creation or reconciliation, never edits an existing deadline."""
    created = 0
    for decision in decisions:
        if decision["operation"] not in {"retain", "review"}:
            continue
        _, added = RetentionReview.objects.get_or_create(
            plan=plan,
            purpose=decision["purpose"],
            defaults={
                "operation": decision["operation"],
                "initial_review_on": date.fromisoformat(decision["review_on"]),
                "next_review_on": date.fromisoformat(decision["review_on"]),
                "responsible_id": plan.action.actor_id,
            },
        )
        created += added
    return created


@sensitive_variables()
def plan_decisions(plan):
    try:
        body = unseal(plan.encrypted_decisions)
        decisions = body["decisions"]
        if body["schema"] != "erasure-plan-v1" or not isinstance(decisions, list):
            raise ValueError
    except (InvalidToken, ValueError, TypeError, KeyError, UnicodeError) as error:
        raise ValidationError("Plan record unavailable / Registro de plan no disponible") from error
    expected = fingerprint(
        canonical(
            {
                "inventory": str(plan.inventory_id),
                "version": plan.action.expected_version,
                "decisions": decisions,
            }
        )
    )
    if expected != plan.action.payload_digest or plan.source_digest != plan.inventory.source_digest:
        raise ValidationError(
            "Plan changed; inspect a valid record / Plan cambiado; consulta registro válido"
        )
    return decisions


def authorized(user, case):
    from apps.core.models import User

    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.mfa_enabled
        or fresh.mfa_version != user.mfa_version
        or fresh.session_version != user.session_version
        or not fresh.has_perm("safety.review_rights_request")
        or not fresh.has_perm("safety.review_retention")
        or not permitted(fresh, case)
    ):
        raise PermissionDenied


@sensitive_variables()
def locked(review_id):
    initial = RetentionReview.objects.select_related("plan__action").get(pk=review_id)
    case, _, _ = locked_case(
        initial.plan.action.request_id,
        lock_listing=True,
        allow_version_change=True,
        allow_erased_account=True,
    )
    review = RetentionReview.objects.select_for_update().get(pk=review_id)
    plan = (
        ErasurePlan.objects.select_for_update()
        .select_related("action", "inventory")
        .get(pk=review.plan_id)
    )
    return case, review, plan


@transaction.atomic
@sensitive_variables()
def record(
    user,
    review_id,
    key,
    version,
    case_version,
    operation,
    reason,
    next_review_on=None,
    history_before=None,
):
    case, review, plan = locked(review_id)
    authorized(user, case)
    if (
        operation not in {"inspect", "follow_up"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError(
            "Record minimized review purpose / Registra motivo minimizado de revisión"
        )
    if history_before is not None and (
        operation != "inspect" or not isinstance(history_before, int) or history_before < 1
    ):
        raise ValidationError("Invalid history cursor / Cursor de historial inválido")
    if operation == "inspect" and next_review_on is not None:
        raise ValidationError("No date for inspection / Consulta sin nueva fecha")
    digest = fingerprint(plan.encrypted_decisions)
    signature = fingerprint(
        canonical(
            {
                "review": str(review.pk),
                "version": version,
                "case_version": case_version,
                "operation": operation,
                "reason": reason,
                "next_review_on": next_review_on,
                "history_before": history_before,
            }
        )
    )
    previous = RetentionReviewEvent.objects.filter(key=key).first()
    if previous:
        if (
            previous.review_id == review.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
            and previous.plan_digest == digest
        ):
            return previous, unseal(previous.encrypted_result) if operation == "inspect" else None
        raise ValidationError("Conflicting review key / Clave de revisión incompatible")
    if (
        review.version != version
        or case.version != case_version
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect current request and review version / Consulta solicitud y versión actual"
        )
    if operation == "follow_up":
        if user.pk == plan.action.actor_id:
            raise PermissionDenied("Independent reviewer required")
        if not isinstance(
            next_review_on, date
        ) or not timezone.localdate() < next_review_on <= timezone.localdate() + timedelta(
            days=365
        ):
            raise ValidationError(
                "Future follow-up within one year / Seguimiento futuro dentro de un año"
            )
        inspections = RetentionReviewEvent.objects.filter(
            review=review,
            actor=user,
            operation="inspect",
            expected_version=version,
            case_version=case_version,
            plan_digest=digest,
        )
        required = set(review.events.filter(operation="follow_up").values_list("pk", flat=True))
        read_ids = set()
        for inspected in inspections:
            read_ids.update(unseal(inspected.encrypted_result)["inspected_follow_up_ids"])
        if not inspections.exists() or not required <= read_ids:
            raise ValidationError(
                "Inspect the current purpose first / Consulta primero la finalidad actual"
            )
    try:
        with transaction.atomic():
            # Audit record precedes disclosure/decryption. Failure rolls everything back.
            event = RetentionReviewEvent.objects.create(
                key=key,
                review=review,
                actor=user,
                expected_version=version,
                case_version=case_version,
                operation=operation,
                plan_digest=digest,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
                next_review_on=next_review_on,
                history_before=history_before,
            )
            decisions = plan_decisions(plan)
            decision = next((row for row in decisions if row["purpose"] == review.purpose), None)
            if (
                not decision
                or decision["operation"] != review.operation
                or decision["review_on"] != review.initial_review_on.isoformat()
            ):
                raise ValidationError("Review scope changed / Ámbito de revisión cambiado")
            disclosed = None
            if operation == "inspect":
                history_query = review.events.filter(operation="follow_up")
                if history_before is not None:
                    history_query = history_query.filter(pk__lt=history_before)
                history_rows = list(history_query.order_by("-pk")[:51])
                history = history_rows[:50]
                disclosed = decision | {
                    "inspected_follow_up_ids": [item.pk for item in history],
                    "next_history_before": history[-1].pk if len(history_rows) > 50 else None,
                    "follow_up_history": [
                        {
                            "reviewed_at": item.created_at.isoformat(),
                            "next_review_on": item.next_review_on.isoformat(),
                            "reason": unseal(item.encrypted_reason)["reason"],
                        }
                        for item in history
                    ],
                }
                event.encrypted_result = seal(disclosed)
                event.save(update_fields=["encrypted_result"])
            else:
                review.next_review_on = next_review_on
                review.responsible = user
                review.last_reviewed_at = timezone.now()
                review.version += 1
                review.save(
                    update_fields=["next_review_on", "responsible", "last_reviewed_at", "version"]
                )
            authorized(user, case)
            return event, disclosed
    except IntegrityError as error:
        raise ValidationError("Review conflict / Conflicto de revisión") from error


@transaction.atomic
@sensitive_variables()
def reconcile(limit=100):
    """Bounded legacy catch-up; no decryption output or automatic deletion."""
    counts = (
        RetentionReview.objects.filter(plan_id=OuterRef("pk"))
        .order_by()
        .values("plan_id")
        .annotate(total=Count("pk"))
        .values("total")
    )
    plans = list(
        ErasurePlan.objects.annotate(
            scheduled_count=Coalesce(Subquery(counts, output_field=IntegerField()), Value(0))
        )
        .select_for_update(skip_locked=True, of=("self",))
        .filter(review_on__isnull=False)
        .filter(
            Q(retention_purpose_count__isnull=True)
            | Q(scheduled_count__lt=F("retention_purpose_count"))
        )
        .select_related("action", "inventory")
        .order_by("created_at", "pk")[:limit]
    )
    scheduled = failed = 0
    for plan in plans:
        try:
            with transaction.atomic():
                decisions = plan_decisions(plan)
                added = schedule(plan, decisions)
                expected = sum(row["operation"] in {"retain", "review"} for row in decisions)
                if plan.retention_purpose_count != expected:
                    plan.retention_purpose_count = expected
                    plan.save(update_fields=["retention_purpose_count"])
            scheduled += added
        except (ValidationError, ValueError, TypeError, KeyError):
            failed += 1
    return {"plans": len(plans), "scheduled": scheduled, "failed": failed}
