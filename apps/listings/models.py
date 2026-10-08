import uuid

from django.contrib.postgres.search import SearchVectorField
from django.db import models

from .search import revision_search_vector
from .text_proof import rate_text_unknown, revision_text_unknown


class Listing(models.Model):
    lifecycle_version = models.PositiveIntegerField(default=1)
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
    source_revision = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="derived_revisions"
    )
    manager_version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, default="draft")
    step = models.PositiveSmallIntegerField(default=1)
    edit_version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    content_language = models.CharField(max_length=2, default="es")
    description_alternative = models.TextField(blank=True)
    search_document = models.GeneratedField(
        expression=revision_search_vector(), output_field=SearchVectorField(), db_persist=True,
    )
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


    class Meta:
        indexes = [models.Index(fields=["id"], name="revision_text_unknown_v1",
                                condition=revision_text_unknown())]


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
        indexes = [models.Index(fields=["id"], name="rate_text_unknown_v1", condition=rate_text_unknown())]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(mode="consult", amount__isnull=True)
                    | models.Q(mode__in=["fixed", "from"], amount__isnull=False, amount__gt=0)
                ),
                name="valid_rate_amount",
            )
        ]


class Submission(models.Model):
    revision = models.OneToOneField(Revision, on_delete=models.PROTECT, related_name="submission")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    approved_base = models.ForeignKey(
        Revision, null=True, blank=True, on_delete=models.PROTECT, related_name="based_submissions"
    )
    document = models.ForeignKey("core.LegalDocument", on_delete=models.PROTECT)
    declaration_version = models.CharField(max_length=32, default="truth-and-rights-v1")
    created_at = models.DateTimeField(auto_now_add=True)


class ModerationDecision(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name="decisions")
    reviewer = models.ForeignKey("core.User", on_delete=models.PROTECT)
    outcome = models.CharField(max_length=12)
    reason = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_listing", "Review listing revisions")]


class Appeal(models.Model):
    decision = models.OneToOneField(
        ModerationDecision, on_delete=models.PROTECT, related_name="appeal"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT, related_name="listing_appeals")
    explanation = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, default="open")
    reviewer = models.ForeignKey(
        "core.User", null=True, on_delete=models.PROTECT, related_name="appeals_reviewed"
    )
    result = models.CharField(max_length=12, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)


class Favorite(models.Model):
    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "listing"], name="one_favorite_per_user_listing"
            )
        ]
        ordering = ["-created_at", "-pk"]


class LifecycleAction(models.Model):
    key = models.UUIDField(unique=True)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="lifecycle_actions")
    actor = models.ForeignKey("core.User", null=True, blank=True, on_delete=models.PROTECT)
    approved_revision = models.ForeignKey(Revision, null=True, blank=True, on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    expected_version = models.PositiveIntegerField()
    confirmed = models.BooleanField(default=False)
    operation = models.CharField(max_length=16)
    previous_status = models.CharField(max_length=12)
    resulting_status = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)


class PublicationState(models.Model):
    """Stored result of the native eligibility rule, excluding expiry (checked in SQL).

    Only trusted when not dirty, computed under the current rules version and for the
    listing's current approved revision. Anything else is evaluated natively per request.
    """

    listing = models.OneToOneField(
        Listing, primary_key=True, on_delete=models.CASCADE, related_name="publication_state"
    )
    eligible = models.BooleanField()
    revision = models.ForeignKey(Revision, null=True, on_delete=models.SET_NULL, related_name="+")
    rules_version = models.CharField(max_length=64)
    check_age = models.BooleanField(default=False)
    check_contact = models.BooleanField(default=False)
    check_agency = models.BooleanField(default=False)
    computed_at = models.DateTimeField()


class PublicationDirty(models.Model):
    """Listings whose stored state may be stale. Written by database triggers only."""

    listing_id = models.UUIDField(primary_key=True)
    generation = models.BigIntegerField()
