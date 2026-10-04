import uuid

from django.db import models
from django.utils import timezone


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_key = models.UUIDField(unique=True)
    receipt_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    listing = models.ForeignKey("listings.Listing", null=True, on_delete=models.SET_NULL)
    revision = models.ForeignKey("listings.Revision", null=True, on_delete=models.SET_NULL)
    reported_agency = models.ForeignKey("core.Agency", null=True, on_delete=models.SET_NULL)
    reported_individual = models.ForeignKey(
        "core.User", null=True, on_delete=models.SET_NULL, related_name="reports_about_management"
    )
    reported_subject = models.ForeignKey(
        "core.User", null=True, on_delete=models.SET_NULL, related_name="reports_about_subject"
    )
    manager_version = models.PositiveIntegerField(null=True)
    mode = models.CharField(max_length=12)
    reason = models.CharField(max_length=20)
    priority = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=16, default="received")
    version = models.PositiveIntegerField(default=1)
    assigned_to = models.ForeignKey(
        "core.User", null=True, on_delete=models.SET_NULL, related_name="assigned_reports"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    receipt_expires_at = models.DateTimeField()

    class Meta:
        permissions = [
            ("review_report", "Review private reports"),
            ("manage_report_assignment", "Manage private report assignments"),
            ("review_restriction", "Independently review publication restrictions"),
        ]
        ordering = ["priority", "created_at", "pk"]


class ReportAccess(models.Model):
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name="accesses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class ReportAction(models.Model):
    key = models.UUIDField(unique=True)
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    operation = models.CharField(max_length=16)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Restriction(models.Model):
    report = models.OneToOneField(Report, on_delete=models.PROTECT)
    listing = models.ForeignKey("listings.Listing", on_delete=models.PROTECT)
    revision = models.ForeignKey("listings.Revision", on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    action = models.OneToOneField(ReportAction, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    review_action = models.OneToOneField(
        ReportAction, null=True, on_delete=models.PROTECT, related_name="reviewed_restriction"
    )
    reviewed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReportNotice(models.Model):
    event_key = models.CharField(max_length=80, unique=True)
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name="notices")
    action = models.ForeignKey(ReportAction, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12)
    encrypted_payload = models.TextField()
    status = models.CharField(max_length=16, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
    simulated_at = models.DateTimeField(null=True)


class SimulatedNoticeDelivery(models.Model):
    notice = models.OneToOneField(ReportNotice, on_delete=models.PROTECT)
    procedure = models.CharField(max_length=32, default="simulator-v1")
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_key = models.UUIDField(unique=True)
    receipt_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=24)
    priority = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, default="received")
    version = models.PositiveIntegerField(default=1)
    assigned_to = models.ForeignKey(
        "core.User", null=True, on_delete=models.SET_NULL, related_name="assigned_rights_requests"
    )
    person = models.ForeignKey(
        "core.Person", null=True, on_delete=models.SET_NULL, related_name="rights_requests"
    )
    referenced_revision = models.ForeignKey(
        "listings.Revision", null=True, on_delete=models.SET_NULL
    )
    manager_version = models.PositiveIntegerField(null=True)
    reported_agency = models.ForeignKey(
        "core.Agency", null=True, on_delete=models.SET_NULL, related_name="rights_requests"
    )
    reported_individual = models.ForeignKey(
        "core.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="rights_requests_about_management",
    )
    reported_subject = models.ForeignKey(
        "core.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="rights_requests_about_subject",
    )
    scope_status = models.CharField(max_length=16, default="unverified")
    created_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField()
    initial_due_at = models.DateTimeField()
    receipt_expires_at = models.DateTimeField()

    @property
    def effective_due_at(self):
        extension = getattr(self, "extension", None)
        return extension.new_due_at if extension else self.initial_due_at

    @property
    def overdue(self):
        return self.status in {"received", "reviewing"} and self.effective_due_at <= timezone.now()

    @property
    def extension_notice_overdue(self):
        # Only receipt publication exists; no delivery adapter is connected yet.
        return bool(
            getattr(self, "extension", None)
            and self.status in {"received", "reviewing"}
            and self.initial_due_at <= timezone.now()
        )

    class Meta:
        permissions = [
            ("review_rights_request", "Review private rights requests"),
            ("manage_rights_assignment", "Manage private rights assignments"),
            ("verify_rights_scope", "Independently verify rights identity and scope"),
            ("execute_rights_request", "Execute scoped private rights requests"),
            ("extend_rights_deadline", "Extend rights response target with recorded grounds"),
        ]
        ordering = ["priority", "initial_due_at", "created_at", "pk"]


class RightsAccess(models.Model):
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="accesses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=200)
    case_version = models.PositiveIntegerField(null=True)
    message_before = models.PositiveBigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsAction(models.Model):
    key = models.UUIDField(unique=True)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    operation = models.CharField(max_length=20)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    clarification_prompt = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsMessage(models.Model):
    key = models.UUIDField(unique=True)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="messages")
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    expected_version = models.PositiveIntegerField()
    payload_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsProof(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.UUIDField(unique=True)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="proofs")
    person = models.ForeignKey("core.Person", on_delete=models.PROTECT)
    initiated_by = models.ForeignKey("core.User", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    manager_version = models.PositiveIntegerField()
    subject_id_snapshot = models.CharField(max_length=64, blank=True)
    scope = models.CharField(max_length=24)
    channel_digest = models.CharField(max_length=64)
    provider = models.CharField(max_length=32)
    procedure = models.CharField(max_length=32)
    status = models.CharField(max_length=12, default="pending")
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()


class RightsProofEvent(models.Model):
    key = models.UUIDField(unique=True)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT, related_name="events")
    verifier = models.ForeignKey("core.User", on_delete=models.PROTECT)
    outcome = models.CharField(max_length=12)
    expected_version = models.PositiveIntegerField()
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsWithdrawal(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", on_delete=models.PROTECT)
    previous_manager_version = models.PositiveIntegerField()
    resulting_manager_version = models.PositiveIntegerField()
    previous_listing_status = models.CharField(max_length=12, blank=True)
    previous_lifecycle_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExportPreview(models.Model):
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    manager_version = models.PositiveIntegerField()
    subject_snapshot = models.CharField(max_length=64, blank=True)
    channel_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    purged_at = models.DateTimeField(null=True)


class RightsExportDownload(models.Model):
    key = models.UUIDField(unique=True)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExtension(models.Model):
    request = models.OneToOneField(
        RightsRequest, on_delete=models.PROTECT, related_name="extension"
    )
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    additional_months = models.PositiveSmallIntegerField()
    reason_code = models.CharField(max_length=12)
    new_due_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
