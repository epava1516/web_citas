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


class Complaint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_key = models.UUIDField(unique=True)
    receipt_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, default="received")
    version = models.PositiveIntegerField(default=1)
    assigned_to = models.ForeignKey(
        "core.User", null=True, on_delete=models.SET_NULL, related_name="assigned_complaints"
    )
    decision = models.ForeignKey("ReportAction", null=True, on_delete=models.PROTECT)
    decision_case_version = models.PositiveIntegerField(null=True)
    listing_decision = models.ForeignKey(
        "listings.ModerationDecision", null=True, on_delete=models.PROTECT
    )
    listing_decision_subject = models.ForeignKey(
        "core.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="complaints_about_listing_subject",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    receipt_expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(decision__isnull=True) | models.Q(listing_decision__isnull=True),
                name="complaint_one_decision_source",
            )
        ]
        permissions = [
            ("review_complaint", "Review private decision complaints"),
            ("manage_complaint_assignment", "Manage decision complaint assignments"),
            ("resolve_complaint", "Resolve independent decision complaints"),
        ]
        ordering = ["created_at", "pk"]


class ComplaintAccess(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="accesses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=200)
    case_version = models.PositiveIntegerField()
    source_version = models.PositiveIntegerField(null=True)
    kind = models.CharField(max_length=12, default="intake")
    photo = models.ForeignKey("mediafiles.Photo", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class ComplaintAction(models.Model):
    key = models.UUIDField(unique=True)
    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    operation = models.CharField(max_length=16)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ComplaintResolution(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.PROTECT, related_name="resolution")
    action = models.OneToOneField(ComplaintAction, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=16)
    encrypted_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ComplaintNotice(models.Model):
    resolution = models.OneToOneField(ComplaintResolution, on_delete=models.PROTECT)
    encrypted_payload = models.TextField()
    status = models.CharField(max_length=16, default="queued")
    recovery_version = models.PositiveIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    error_code = models.CharField(max_length=32, blank=True)
    simulated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SimulatedComplaintNoticeDelivery(models.Model):
    notice = models.OneToOneField(ComplaintNotice, on_delete=models.PROTECT)
    procedure = models.CharField(max_length=32, default="simulator-v1")
    created_at = models.DateTimeField(auto_now_add=True)


class ReportAccess(models.Model):
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name="accesses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=200)
    case_version = models.PositiveIntegerField(null=True)
    action_before = models.PositiveBigIntegerField(null=True)
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
    recovery_version = models.PositiveIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    error_code = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    simulated_at = models.DateTimeField(null=True)


class NoticeRecovery(models.Model):
    key = models.UUIDField(unique=True)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    rights_notice = models.ForeignKey("RightsNotice", null=True, on_delete=models.PROTECT)
    report_notice = models.ForeignKey(ReportNotice, null=True, on_delete=models.PROTECT)
    complaint_notice = models.ForeignKey(ComplaintNotice, null=True, on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    previous_attempts = models.PositiveSmallIntegerField()
    encrypted_reason = models.TextField()
    payload_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("manage_notice_delivery", "Recover failed private notices")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        report_notice__isnull=False,
                        complaint_notice__isnull=True,
                        rights_notice__isnull=True,
                    )
                    | models.Q(
                        report_notice__isnull=True,
                        complaint_notice__isnull=False,
                        rights_notice__isnull=True,
                    )
                    | models.Q(
                        report_notice__isnull=True,
                        complaint_notice__isnull=True,
                        rights_notice__isnull=False,
                    )
                ),
                name="notice_recovery_exactly_one_source",
            )
        ]


class SimulatedNoticeDelivery(models.Model):
    notice = models.OneToOneField(ReportNotice, on_delete=models.PROTECT)
    procedure = models.CharField(max_length=32, default="simulator-v1")
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRequest(models.Model):
    response_version = models.PositiveIntegerField(default=0)
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


class RightsResponse(models.Model):
    key = models.UUIDField(unique=True)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="responses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    response_version = models.PositiveIntegerField()
    kind = models.CharField(max_length=24)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    encrypted_response = models.TextField()
    withdrawal = models.OneToOneField("RightsWithdrawal", null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("respond_rights_request", "Issue private motivated rights responses")]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "response_version"], name="rights_response_sequence_once"
            )
        ]


class RightsNotice(models.Model):
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    encrypted_payload = models.TextField()
    status = models.CharField(max_length=16, default="queued")
    recovery_version = models.PositiveIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    error_code = models.CharField(max_length=32, blank=True)
    simulated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SimulatedRightsNoticeDelivery(models.Model):
    notice = models.OneToOneField(RightsNotice, on_delete=models.PROTECT)
    procedure = models.CharField(max_length=32, default="simulator-v1")
    created_at = models.DateTimeField(auto_now_add=True)


class RightsAccess(models.Model):
    response_version = models.PositiveIntegerField(null=True)
    response_before = models.PositiveBigIntegerField(null=True)
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


class PrivacyPublicationHold(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey(
        "core.Person", on_delete=models.PROTECT, related_name="privacy_publication_holds"
    )
    subject_snapshot = models.CharField(max_length=64)
    manager_version = models.PositiveIntegerField()
    ground = models.CharField(max_length=24)
    active = models.BooleanField(default=True)
    previous_listing_status = models.CharField(max_length=12, blank=True)
    previous_lifecycle_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["person", "active"])]


class ErasureInventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_manifest = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ErasurePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(ErasureInventory, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_decisions = models.TextField()
    review_on = models.DateField(null=True, db_index=True)
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


class RightsImageAccess(models.Model):
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    photo = models.ForeignKey("mediafiles.Photo", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    content_digest = models.CharField(max_length=64)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExportImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT, related_name="images")
    photo = models.ForeignKey("mediafiles.Photo", on_delete=models.PROTECT)
    encrypted_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["export", "photo"], name="rights_export_photo_once")
        ]


class RightsExportDownload(models.Model):
    image = models.ForeignKey(RightsExportImage, null=True, on_delete=models.PROTECT)
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
