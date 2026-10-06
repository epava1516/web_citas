"""Prepared synthetic commercial records; no provider or live checkout."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class PromotionOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    listing = models.ForeignKey("listings.Listing", on_delete=models.PROTECT)
    product_version = models.ForeignKey("catalog.PromotionProductVersion", on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    request_digest = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    kind = models.CharField(
        max_length=16, choices=[("premium", "Premium"), ("top", "Top"), ("autobump", "Auto bump")]
    )
    duration_days = models.PositiveSmallIntegerField()
    bump_interval_minutes = models.PositiveSmallIntegerField(null=True)
    daily_bump_limit = models.PositiveSmallIntegerField(null=True)
    status = models.CharField(
        max_length=12,
        default="pending",
        choices=[("pending", "Pending"), ("paid", "Synthetic paid"), ("cancelled", "Cancelled")],
    )
    synthetic = models.BooleanField(default=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["buyer", "idempotency_key"], name="promotion_order_actor_key_unique"
            ),
            models.CheckConstraint(
                condition=Q(
                    synthetic=True,
                    currency="EUR",
                    amount__gt=0,
                    net_amount__gt=0,
                    tax_amount__gte=0,
                    tax_rate__gte=0,
                    tax_rate__lte=100,
                    duration_days__gt=0,
                    manager_version__gt=0,
                ),
                name="promotion_order_synthetic_valid",
            ),
            models.CheckConstraint(
                condition=Q(amount=F("net_amount") + F("tax_amount")),
                name="promotion_order_amount_sum",
            ),
        ]


class PromotionPaymentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        PromotionOrder, on_delete=models.PROTECT, related_name="payment_attempt"
    )
    status = models.CharField(
        max_length=12,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("failed", "Failed"),
            ("succeeded", "Synthetic succeeded"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class PromotionPaymentEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(PromotionPaymentAttempt, on_delete=models.PROTECT)
    event_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    outcome = models.CharField(
        max_length=12,
        choices=[
            ("pending", "Pending"),
            ("failed", "Failed"),
            ("succeeded", "Synthetic succeeded"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class PromotionEntitlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        PromotionOrder, on_delete=models.PROTECT, related_name="entitlement"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    suspended_at = models.DateTimeField(null=True)
    last_bumped_at = models.DateTimeField(null=True)
    last_checked_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="promotion_entitlement_positive_window",
            )
        ]


class PromotionBumpExecution(models.Model):
    entitlement = models.ForeignKey(PromotionEntitlement, on_delete=models.PROTECT)
    window_start = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entitlement", "window_start"], name="promotion_bump_window_unique"
            )
        ]


class PromotionOrderAudit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    order = models.ForeignKey(PromotionOrder, on_delete=models.PROTECT)
    operation = models.CharField(max_length=24)
    payload_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
