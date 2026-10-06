"""Commercial dependent evidence; no implicit erasure or agency-wide authority."""

from django.db.models import Q


def specs(*, person=None, user=None):
    if (person is None) == (user is None):
        raise ValueError("One exact inventory subject required")
    order_scope = Q(listing__person=person) if person is not None else Q(buyer=user)
    if user is not None:
        order_scope |= Q(listing__person__subject=user) | Q(listing__person__individual=user)
    from apps.catalog.promotion_order_models import PromotionOrder

    order_ids = PromotionOrder.objects.filter(order_scope).values("pk")
    audit_scope = Q(order_id__in=order_ids)
    if user is not None:
        audit_scope |= Q(actor=user)
    elif person.subject_id:
        audit_scope |= Q(actor_id=person.subject_id)
    definitions = [
        (
            "PromotionOrder",
            order_scope,
            [
                "pk",
                "buyer_id",
                "listing_id",
                "product_version_id",
                "manager_version",
                "request_digest",
                "amount",
                "currency",
                "tax_rate",
                "tax_amount",
                "net_amount",
                "kind",
                "duration_days",
                "bump_interval_minutes",
                "daily_bump_limit",
                "status",
                "synthetic",
                "created_at",
            ],
        ),
        (
            "PromotionPaymentAttempt",
            Q(order_id__in=order_ids),
            ["pk", "order_id", "status", "created_at"],
        ),
        (
            "PromotionPaymentEvent",
            Q(attempt__order_id__in=order_ids),
            ["pk", "attempt_id", "payload_digest", "outcome", "created_at"],
        ),
        (
            "PromotionEntitlement",
            Q(order_id__in=order_ids),
            ["pk", "order_id", "starts_at", "ends_at", "suspended_at", "last_bumped_at"],
        ),
        (
            "PromotionBumpExecution",
            Q(entitlement__order_id__in=order_ids),
            ["pk", "entitlement_id", "window_start", "created_at"],
        ),
        (
            "PromotionOrderAudit",
            audit_scope,
            ["pk", "actor_id", "order_id", "operation", "payload_digest", "created_at"],
        ),
    ]
    return [
        ("catalog." + name, scope, "dependent_evidence", fields)
        for name, scope, fields in definitions
    ]
