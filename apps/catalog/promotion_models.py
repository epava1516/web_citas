"""Nonpersonal promotion catalogue; customer purchases and live payments are absent."""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class PromotionProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=64, unique=True)
    kind = models.CharField(
        max_length=16,
        choices=[
            ("premium", "Premium"),
            ("top", "Top"),
            ("autobump", "Autosubida / Auto bump"),
        ],
    )
    active = models.BooleanField(default=True)

    class Meta:
        permissions = [("manage_promotion_products", "Manage promotion product catalogue")]
        ordering = ["slug", "pk"]


class PromotionProductVersion(models.Model):
    product = models.ForeignKey(PromotionProduct, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    edit_version = models.PositiveIntegerField(default=1)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    duration_days = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, choices=[("EUR", "EUR")])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bump_interval_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    daily_bump_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, editable=False)
    is_current = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-version", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "version"], name="promotion_product_version_unique"
            ),
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_current=True),
                name="promotion_product_current_unique",
            ),
            models.CheckConstraint(
                condition=Q(version__gt=0, edit_version__gt=0, duration_days__gt=0),
                name="promotion_version_positive",
            ),
            models.CheckConstraint(
                condition=Q(amount__isnull=True) | Q(amount__gt=0), name="promotion_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(tax_rate__isnull=True) | Q(tax_rate__gte=0, tax_rate__lte=100),
                name="promotion_tax_range",
            ),
            models.CheckConstraint(
                condition=Q(bump_interval_minutes__isnull=True) | Q(bump_interval_minutes__gt=0),
                name="promotion_interval_positive",
            ),
            models.CheckConstraint(
                condition=Q(daily_bump_limit__isnull=True) | Q(daily_bump_limit__gt=0),
                name="promotion_daily_limit_positive",
            ),
            models.CheckConstraint(
                condition=Q(is_current=False) | Q(published_at__isnull=False),
                name="promotion_current_published",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.product_id
            and self.product.kind != "autobump"
            and (self.bump_interval_minutes is not None or self.daily_bump_limit is not None)
        ):
            raise ValidationError(
                "Frecuencia y cupo solo para autosubida / Bump settings require auto bump"
            )

    @property
    def configuration_ready(self):
        return bool(
            self.amount is not None
            and self.amount > Decimal("0")
            and self.currency == "EUR"
            and self.tax_rate is not None
            and 0 <= self.tax_rate <= 100
            and (
                self.product.kind != "autobump"
                or (self.bump_interval_minutes and self.daily_bump_limit)
            )
        )

    @property
    def sellable(self):
        # v1 deliberately has no checkout or provider connection.
        return False


class PromotionCatalogueAudit(models.Model):
    """Operator evidence; no customer or free-text request payload."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    product_version = models.ForeignKey(PromotionProductVersion, on_delete=models.PROTECT)
    operation = models.CharField(
        max_length=16,
        choices=[
            ("create_product", "Create product"),
            ("create_version", "Create version"),
            ("update_version", "Update version"),
            ("publish_version", "Publish version"),
        ],
    )
    edit_version = models.PositiveIntegerField()
    payload_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
