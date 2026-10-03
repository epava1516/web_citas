import uuid

from django.db import models


class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.OneToOneField("core.Person", on_delete=models.PROTECT, related_name="listing")
    status = models.CharField(
        max_length=12,
        default="draft",
        choices=[
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("pending", "Pending"),
            ("published", "Published"),
            ("paused", "Paused"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
            ("expired", "Expired"),
        ],
    )
    approved_revision = models.ForeignKey(
        "Revision", null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_for"
    )
    published_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)
    available_until = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Revision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="revisions")
    manager_version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, default="draft")
    step = models.PositiveSmallIntegerField(default=1)
    edit_version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    content_language = models.CharField(max_length=2, default="es")
    description_alternative = models.TextField(blank=True)
    profile_type = models.CharField(max_length=20, default="woman")
    categories = models.ManyToManyField("catalog.Category")
    services = models.ManyToManyField("catalog.Service")
    municipality = models.ForeignKey(
        "catalog.Municipality", null=True, blank=True, on_delete=models.PROTECT
    )
    postal_code = models.ForeignKey(
        "catalog.PostalCode", null=True, blank=True, on_delete=models.PROTECT
    )
    zone = models.ForeignKey("catalog.Zone", null=True, blank=True, on_delete=models.PROTECT)
    travel_areas = models.ManyToManyField(
        "catalog.Municipality", related_name="travel_revisions", blank=True
    )
    spoken_languages = models.JSONField(default=list)
    days = models.JSONField(default=list)
    time_slot = models.CharField(max_length=20, blank=True)
    reception = models.BooleanField(default=False)
    travel = models.BooleanField(default=False)
    phone = models.CharField(max_length=16, blank=True)
    whatsapp = models.BooleanField(default=False)
    telegram = models.CharField(max_length=32, blank=True)
    contact_exposure_accepted = models.BooleanField(default=False)
    publisher_acceptance = models.ForeignKey(
        "core.LegalAcceptance", null=True, blank=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Rate(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE, related_name="rates")
    concept = models.CharField(max_length=80)
    mode = models.CharField(
        max_length=12, choices=[("fixed", "Fixed"), ("from", "From"), ("consult", "Consult")]
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="EUR")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(mode="consult", amount__isnull=True)
                    | models.Q(mode__in=["fixed", "from"], amount__isnull=False, amount__gt=0)
                ),
                name="valid_rate_amount",
            )
        ]
