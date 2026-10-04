import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    account_erased_at = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(
        max_length=20,
        default="visitor",
        choices=[("visitor", "Visitor"), ("individual", "Individual"), ("agency", "Agency")],
    )
    mfa_secret_encrypted = models.TextField(blank=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_last_counter = models.BigIntegerField(default=-1)
    mfa_version = models.PositiveIntegerField(default=0)
    session_version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="user_email_case_insensitive")]


class LegalDocument(models.Model):
    slug = models.SlugField()
    version = models.CharField(max_length=32)
    language = models.CharField(max_length=2, choices=[("es", "ES"), ("en", "EN")])
    title = models.CharField(max_length=200)
    body = models.TextField()
    published_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "version", "language"], name="legal_version_language"
            ),
            models.UniqueConstraint(
                fields=["slug", "language"],
                condition=models.Q(active=True),
                name="legal_one_active",
            ),
        ]


class LegalAcceptance(models.Model):
    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(LegalDocument, on_delete=models.PROTECT)
    action = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "document", "action", "agency"],
                name="legal_accept_once",
                nulls_distinct=False,
            )
        ]


class AccountToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    user_state = models.CharField(max_length=64, default="")
    purpose = models.CharField(max_length=12, choices=[("verify", "Verify"), ("reset", "Reset")])
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RateWindow(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField()


class RecoveryCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(null=True)


class Agency(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    owner = models.OneToOneField(User, on_delete=models.PROTECT, related_name="owned_agency")
    created_at = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(max_length=12, default="pending")
    verification_procedure = models.CharField(max_length=32, blank=True)
    review_version = models.PositiveIntegerField(default=1)


class AgencyReview(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=12)
    reason = models.CharField(max_length=500)
    evidence_reference = models.CharField(max_length=80)
    procedure = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_agency", "Review organization verification")]


class AgencyMember(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agency_memberships")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["agency", "user"], name="agency_member_unique")
        ]


class AgencyInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    email = models.EmailField()
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True)
    revoked_at = models.DateTimeField(null=True)


class Person(models.Model):
    publication_erased_at = models.DateTimeField(null=True, blank=True)
    rights_version = models.PositiveIntegerField(default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alias = models.CharField(max_length=80)
    individual = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.PROTECT, related_name="individual_person"
    )
    agency = models.ForeignKey(
        Agency, null=True, blank=True, on_delete=models.PROTECT, related_name="people"
    )
    assigned_editor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_people"
    )
    subject = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.PROTECT, related_name="represented_person"
    )
    manager_version = models.PositiveIntegerField(default=1)
    manager_review_status = models.CharField(max_length=12, default="approved")
    age_status = models.CharField(
        max_length=12,
        default="pending",
        choices=[("pending", "Pending"), ("passed", "Passed"), ("failed", "Failed")],
    )
    consent_version = models.PositiveIntegerField(default=0)
    consent_revoked_at = models.DateTimeField(null=True, blank=True)
    phone_claim = models.ForeignKey("PhoneClaim", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(individual__isnull=False, agency__isnull=True)
                    | models.Q(individual__isnull=True, agency__isnull=False)
                ),
                name="person_exactly_one_manager",
            )
        ]


class PhoneClaim(models.Model):
    verification_procedure = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=16, unique=True)
    individual = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    agency = models.ForeignKey(Agency, null=True, blank=True, on_delete=models.PROTECT)
    verified_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(individual__isnull=False, agency__isnull=True)
                    | models.Q(individual__isnull=True, agency__isnull=False)
                ),
                name="phone_exactly_one_manager",
            )
        ]


class ManagerReview(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="manager_reviews")
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    outcome = models.CharField(max_length=12)
    reason = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "manager_version"], name="one_manager_review_per_version"
            )
        ]


class PhoneChallenge(models.Model):
    person_rights_version = models.PositiveIntegerField(default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    manager_version = models.PositiveIntegerField()
    digest = models.CharField(max_length=64)
    phone = models.CharField(max_length=16)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)


class VerificationCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    subject = models.ForeignKey(User, on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    provider = models.CharField(max_length=32)
    procedure = models.CharField(max_length=32, default="simulator-v1")
    status = models.CharField(max_length=12, default="pending")
    completed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class VerificationEvent(models.Model):
    event_id = models.UUIDField(primary_key=True)
    verification = models.ForeignKey(VerificationCheck, on_delete=models.CASCADE)
    outcome = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)


class RepresentationInvitation(models.Model):
    person_rights_version = models.PositiveIntegerField(default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    email = models.EmailField()
    manager_version = models.PositiveIntegerField()
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True)


class RepresentationAction(models.Model):
    previous_manager_kind = models.CharField(max_length=12, default="")
    previous_manager_id = models.CharField(max_length=64, default="")
    manager_kind = models.CharField(max_length=12, default="")
    manager_id = models.CharField(max_length=64, default="")
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    subject = models.ForeignKey(User, on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    action = models.CharField(max_length=16)
    document = models.ForeignKey(LegalDocument, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.manager_id:
            self.manager_kind = "agency" if self.person.agency_id else "individual"
            self.manager_id = str(self.person.agency_id or self.person.individual_id)
        super().save(*args, **kwargs)


class ManagerAppeal(models.Model):
    decision = models.OneToOneField(ManagerReview, on_delete=models.PROTECT, related_name="appeal")
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="manager_appeals")
    explanation = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, default="open")
    reviewer = models.ForeignKey(
        User, null=True, on_delete=models.PROTECT, related_name="manager_appeals_reviewed"
    )
    result = models.CharField(max_length=12, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)


class AgencyAppeal(models.Model):
    decision = models.OneToOneField(AgencyReview, on_delete=models.PROTECT, related_name="appeal")
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="agency_appeals")
    review_version = models.PositiveIntegerField()
    explanation = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, default="open")
    reviewer = models.ForeignKey(
        User, null=True, on_delete=models.PROTECT, related_name="agency_appeals_reviewed"
    )
    result = models.CharField(max_length=12, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
