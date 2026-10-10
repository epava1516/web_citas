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


class UrgentReportAlert(models.Model):
    report = models.OneToOneField(Report, on_delete=models.PROTECT, related_name="urgent_alert")
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True)
    acknowledged_by = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(acknowledged_at__isnull=True, acknowledged_by__isnull=True)
                    | models.Q(acknowledged_at__isnull=False, acknowledged_by__isnull=False)
                ),
                name="urgent_report_ack_pair",
            )
        ]


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
    message_before = models.PositiveBigIntegerField(null=True)
    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="accesses")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=200)
    case_version = models.PositiveIntegerField()
    source_version = models.PositiveIntegerField(null=True)
    kind = models.CharField(max_length=12, default="intake")
    photo = models.ForeignKey("mediafiles.Photo", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class ComplaintAction(models.Model):
    clarification_prompt = models.CharField(max_length=24, blank=True)
    key = models.UUIDField(unique=True)
    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    operation = models.CharField(max_length=16)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ComplaintMessage(models.Model):
    key = models.UUIDField(unique=True)
    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="messages")
    actor = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    expected_version = models.PositiveIntegerField()
    payload_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
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
    account_subject = models.ForeignKey(
        "core.User", null=True, on_delete=models.PROTECT, related_name="account_rights_requests"
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
        constraints = [
            models.CheckConstraint(
                condition=models.Q(account_subject__isnull=True)
                | (models.Q(person__isnull=True) & models.Q(referenced_revision__isnull=True)),
                name="rights_account_scope_excludes_profile",
            ),
        ]
        permissions = [
            ("review_rights_request", "Review private rights requests"),
            ("manage_rights_assignment", "Manage private rights assignments"),
            ("verify_rights_scope", "Independently verify rights identity and scope"),
            ("execute_rights_request", "Execute scoped private rights requests"),
            ("extend_rights_deadline", "Extend rights response target with recorded grounds"),
            ("review_privacy_hold", "Independently review privacy publication holds"),
            ("review_rectification", "Independently review proposed data corrections"),
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
    purged_at = models.DateTimeField(null=True, blank=True)
    final_response = models.ForeignKey(
        "RightsResponse",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="final_audit_actions",
    )
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
    person_rights_version = models.PositiveIntegerField(default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.UUIDField(unique=True)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT, related_name="proofs")
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey(
        "core.User", null=True, on_delete=models.PROTECT, related_name="account_rights_proofs"
    )
    account_source_digest = models.CharField(max_length=64, blank=True)
    initiated_by = models.ForeignKey("core.User", on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    manager_version = models.PositiveIntegerField(null=True)
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="rights_proof_exactly_one_scope",
            ),
        ]


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


class RightsResponseAcknowledgement(models.Model):
    response = models.OneToOneField(
        RightsResponse, on_delete=models.PROTECT, related_name="receipt_acknowledgement"
    )
    channel_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class PrivacyPublicationHold(models.Model):
    version = models.PositiveIntegerField(default=1)
    purpose_review_on = models.DateField(null=True, db_index=True)
    initial_purpose_review_on = models.DateField(null=True)
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


class PublicationCalendarEvent(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    hold = models.ForeignKey(
        PrivacyPublicationHold,
        on_delete=models.PROTECT,
        related_name="calendar_events",
    )
    expected_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class PrivacyHoldReleaseProposal(models.Model):
    purpose_read = models.ForeignKey(
        RightsAction,
        null=True,
        on_delete=models.PROTECT,
        related_name="publication_release_proposals",
    )
    ground = models.CharField(max_length=24, blank=True)
    resume_message = models.ForeignKey(RightsMessage, null=True, on_delete=models.PROTECT)
    released_proof = models.ForeignKey(
        RightsProof, null=True, on_delete=models.PROTECT, related_name="privacy_hold_releases"
    )
    hold = models.ForeignKey(
        PrivacyPublicationHold, on_delete=models.PROTECT, related_name="release_proposals"
    )
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    released_action = models.OneToOneField(
        RightsAction, null=True, on_delete=models.PROTECT, related_name="privacy_hold_release"
    )
    released_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ErasureInventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_manifest = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="erasure_inventory_exactly_one_scope",
            ),
        ]


class ErasurePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(ErasureInventory, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_decisions = models.TextField()
    review_on = models.DateField(null=True, db_index=True)
    retention_purpose_count = models.PositiveSmallIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RetentionReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        ErasurePlan, on_delete=models.PROTECT, related_name="retention_reviews"
    )
    purpose = models.CharField(max_length=40)
    operation = models.CharField(max_length=10)
    initial_review_on = models.DateField()
    next_review_on = models.DateField(db_index=True)
    responsible = models.ForeignKey("core.User", on_delete=models.PROTECT)
    version = models.PositiveIntegerField(default=1)
    last_reviewed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_retention", "Independently review per-purpose retention follow-up")]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "purpose"], name="retention_review_one_purpose"
            ),
            models.CheckConstraint(
                condition=models.Q(operation__in=["retain", "review"]),
                name="retention_review_supported_operation",
            ),
        ]


class RetentionReviewEvent(models.Model):
    key = models.UUIDField(unique=True)
    review = models.ForeignKey(RetentionReview, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    expected_version = models.PositiveIntegerField()
    case_version = models.PositiveIntegerField()
    operation = models.CharField(max_length=12)
    history_before = models.PositiveBigIntegerField(null=True)
    plan_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    encrypted_reason = models.TextField()
    encrypted_result = models.TextField(default="")
    next_review_on = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(operation__in=["inspect", "follow_up"]),
                name="retention_event_supported_operation",
            )
        ]


class ErasureExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.OneToOneField(ErasurePlan, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    encrypted_result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="erasure_execution_exactly_one_scope",
            ),
        ]


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
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    manager_version = models.PositiveIntegerField(null=True)
    subject_snapshot = models.CharField(max_length=64, blank=True)
    channel_digest = models.CharField(max_length=64)
    encrypted_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    purged_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="rights_export_exactly_one_scope",
            ),
        ]


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


class RightsExportPart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT, related_name="parts")
    position = models.PositiveIntegerField()
    encrypted_content = models.TextField()
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["export", "position"], name="rights_export_part_position_once"
            )
        ]


class RightsExportDownload(models.Model):
    part = models.ForeignKey(RightsExportPart, null=True, on_delete=models.PROTECT)
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


class RightsRectificationProposal(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    source_revision = models.ForeignKey("listings.Revision", null=True, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_changes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (
                    models.Q(person__isnull=True)
                    & models.Q(account_subject__isnull=False)
                    & models.Q(source_revision__isnull=True)
                ),
                name="rectification_proposal_exactly_one_scope",
            ),
        ]


class RightsRectificationPhotoUpload(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    photo = models.OneToOneField(
        "mediafiles.Photo", on_delete=models.PROTECT, related_name="rectification_upload"
    )
    source_digest = models.CharField(max_length=64)
    person_rights_version = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    discarded_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationSourceRead(models.Model):
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationProposalRead(models.Model):
    proposal = models.ForeignKey(RightsRectificationProposal, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    changes_digest = models.CharField(max_length=64)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationReview(models.Model):
    proposal = models.OneToOneField(RightsRectificationProposal, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=12)
    changes_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationNotification(models.Model):
    review = models.OneToOneField(RightsRectificationReview, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationExecution(models.Model):
    notification = models.OneToOneField(RightsRectificationNotification, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, null=True, on_delete=models.PROTECT)
    corrected_revision = models.OneToOneField(
        "listings.Revision", null=True, on_delete=models.PROTECT
    )
    encrypted_previous_values = models.TextField()
    resulting_rights_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationManagerNotice(models.Model):
    execution = models.ForeignKey(RightsRectificationExecution, on_delete=models.PROTECT)
    recipient = models.ForeignKey("core.User", on_delete=models.PROTECT)
    manager_version = models.PositiveIntegerField()
    acknowledged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "recipient"], name="rectification_manager_notice_once"
            )
        ]


class RightsRectificationRecipientInventory(models.Model):
    execution = models.ForeignKey(RightsRectificationExecution, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_inventory = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationRecipientAssessment(models.Model):
    inventory = models.ForeignKey(RightsRectificationRecipientInventory, on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_decisions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("review_recipient_assessment", "Independently review recipient assessments")
        ]


class RightsRectificationRecipientReview(models.Model):
    assessment = models.OneToOneField(
        RightsRectificationRecipientAssessment, on_delete=models.PROTECT
    )
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=12)
    source_digest = models.CharField(max_length=64)
    decisions_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRectificationPhotoDisposition(models.Model):
    execution = models.ForeignKey(
        RightsRectificationExecution, on_delete=models.PROTECT, related_name="photo_dispositions"
    )
    source_photo = models.ForeignKey("mediafiles.Photo", on_delete=models.PROTECT)
    blob = models.ForeignKey("mediafiles.Blob", on_delete=models.PROTECT)
    outcome = models.CharField(
        max_length=12, choices=[("retained", "Retained"), ("withdrawn", "Withdrawn")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "source_photo"], name="rectification_photo_disposition_once"
            ),
            models.CheckConstraint(
                condition=models.Q(outcome__in=["retained", "withdrawn"]),
                name="rectification_photo_disposition_outcome",
            ),
        ]


class RightsPhotoReintroduction(models.Model):
    review_version = models.PositiveIntegerField(default=1)
    photo = models.ForeignKey("mediafiles.Photo", on_delete=models.PROTECT)
    uploaded_blob = models.ForeignKey("mediafiles.Blob", on_delete=models.PROTECT)
    disposition = models.ForeignKey(RightsRectificationPhotoDisposition, on_delete=models.PROTECT)
    method = models.CharField(
        max_length=16, choices=[("sha256", "Exact bytes"), ("regional", "Visual candidate")]
    )
    score = models.FloatField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["photo", "disposition"], name="rights_photo_reintroduction_once"
            ),
            models.CheckConstraint(
                condition=models.Q(method__in=["sha256", "regional"]),
                name="rights_photo_reintroduction_method",
            ),
        ]
        permissions = [
            ("review_photo_reintroduction", "Independently review protected photo reuse")
        ]


class RightsPhotoReintroductionRead(models.Model):
    key = models.UUIDField(unique=True)
    candidate = models.ForeignKey(RightsPhotoReintroduction, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    review_version = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    purpose = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsPhotoReintroductionDecision(models.Model):
    key = models.UUIDField(unique=True)
    read = models.ForeignKey(RightsPhotoReintroductionRead, on_delete=models.PROTECT)
    candidate = models.ForeignKey(
        RightsPhotoReintroduction, on_delete=models.PROTECT, related_name="decisions"
    )
    review_version = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    outcome = models.CharField(
        max_length=16,
        choices=[
            ("maintain", "Maintain withdrawal"),
            ("false_positive", "Visual false positive"),
            ("authorize", "Authorize current use"),
        ],
    )
    encrypted_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "review_version"], name="rights_reuse_decision_version_once"
            ),
            models.CheckConstraint(
                condition=models.Q(outcome__in=["maintain", "false_positive", "authorize"]),
                name="rights_reuse_decision_outcome",
            ),
        ]


class RightsAccountEmailConfirmation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proposal = models.ForeignKey(RightsRectificationProposal, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    subject = models.ForeignKey("core.User", on_delete=models.PROTECT)
    digest = models.CharField(max_length=64, unique=True)
    source_digest = models.CharField(max_length=64)
    destination_digest = models.CharField(max_length=64)
    encrypted_delivery = models.TextField()
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProcessingPurposePlan(models.Model):
    """Reviewed preparation only; enforcement and final response are separate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="processing_plan_exactly_one_scope",
            ),
        ]


class ProcessingPlanRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    plan = models.ForeignKey(ProcessingPurposePlan, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    plan_digest = models.CharField(max_length=64)
    source_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class ProcessingPlanReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    plan = models.OneToOneField(ProcessingPurposePlan, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    plan_digest = models.CharField(max_length=64)
    source_digest = models.CharField(max_length=64)
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_processing_plan", "Independently review purpose processing plans")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="processing_review_valid_outcome",
            )
        ]


class ProcessingExecution(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    review = models.ForeignKey(ProcessingPlanReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    person = models.ForeignKey("core.Person", null=True, on_delete=models.PROTECT)
    account_subject = models.ForeignKey("core.User", null=True, on_delete=models.PROTECT)
    publication_hold = models.OneToOneField(
        PrivacyPublicationHold,
        null=True,
        on_delete=models.PROTECT,
        related_name="purpose_execution",
    )
    source_digest = models.CharField(max_length=64)
    encrypted_result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(person__isnull=False) & models.Q(account_subject__isnull=True))
                | (models.Q(person__isnull=True) & models.Q(account_subject__isnull=False)),
                name="processing_execution_exact_scope",
            )
        ]


class PurposeRestriction(models.Model):
    version = models.PositiveIntegerField(default=1)
    initial_review_on = models.DateField(null=True)
    execution = models.ForeignKey(ProcessingExecution, on_delete=models.PROTECT)
    subject = models.ForeignKey("core.User", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=40)
    mode = models.CharField(max_length=10)
    review_on = models.DateField(db_index=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "purpose"], name="purpose_restriction_once"
            ),
            models.CheckConstraint(
                condition=models.Q(mode__in=["restrict", "cease"]),
                name="purpose_restriction_valid_mode",
            ),
        ]


class PurposeRestrictionRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    restriction = models.ForeignKey(PurposeRestriction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class PurposeReleaseProposal(models.Model):
    restriction = models.ForeignKey(
        PurposeRestriction, on_delete=models.PROTECT, related_name="release_proposals"
    )
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    ground = models.CharField(max_length=24)
    resume_message = models.ForeignKey(RightsMessage, null=True, on_delete=models.PROTECT)
    released_action = models.OneToOneField(
        RightsAction, null=True, on_delete=models.PROTECT, related_name="purpose_release_execution"
    )
    released_proof = models.ForeignKey(
        RightsProof, null=True, on_delete=models.PROTECT, related_name="purpose_releases"
    )
    released_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("release_purpose_restriction", "Independently propose and execute purpose releases")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ground__in=["restriction_resolved", "resume_requested"]),
                name="purpose_release_valid_ground",
            )
        ]


class PurposeCalendarEvent(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    restriction = models.ForeignKey(
        PurposeRestriction, on_delete=models.PROTECT, related_name="calendar_events"
    )
    expected_version = models.PositiveIntegerField()
    encrypted_snapshot = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("review_purpose_calendar", "Review operational purpose restriction calendar")
        ]


class PurposeExceptionProposal(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    subject = models.ForeignKey("core.User", on_delete=models.PROTECT)
    plan = models.ForeignKey(ErasurePlan, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    encrypted_scope = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("review_purpose_exception", "Independently review scoped processing exceptions")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("created_at")),
                name="purpose_exception_future_expiry",
            )
        ]


class PurposeExceptionRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proposal = models.ForeignKey(PurposeExceptionProposal, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class PurposeExceptionReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proposal = models.OneToOneField(PurposeExceptionProposal, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    outcome = models.CharField(max_length=10)
    consumed_action = models.OneToOneField(
        RightsAction,
        null=True,
        on_delete=models.PROTECT,
        related_name="purpose_exception_consumption",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="purpose_exception_valid_outcome",
            ),
            models.CheckConstraint(
                condition=models.Q(consumed_action__isnull=True) | models.Q(outcome="approved"),
                name="purpose_exception_only_approved_consumed",
            ),
        ]


class RightsCopyPageReview(models.Model):
    request = models.ForeignKey(
        RightsRequest, on_delete=models.PROTECT, related_name="copy_page_reviews"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    action = models.OneToOneField(
        RightsAction, on_delete=models.PROTECT, related_name="copy_page_review"
    )
    read_action = models.ForeignKey(
        RightsAction, on_delete=models.PROTECT, related_name="copy_page_review_reads"
    )
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    section = models.CharField(max_length=32)
    page = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    encrypted_entries = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "actor", "source_digest", "section", "page", "version"],
                name="copy_page_review_version_once",
            ),
            models.CheckConstraint(
                condition=models.Q(page__gte=1, version__gte=1),
                name="copy_page_review_positive_versions",
            ),
        ]


class RightsCopyInformation(models.Model):
    request = models.ForeignKey(
        RightsRequest, on_delete=models.PROTECT, related_name="copy_information"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    policy_document = models.ForeignKey("core.LegalDocument", null=True, on_delete=models.PROTECT)
    policy_digest = models.CharField(max_length=64, blank=True, default="")
    policy_version = models.CharField(max_length=80)
    original_session_version = models.PositiveIntegerField(null=True)
    original_mfa_version = models.PositiveIntegerField(null=True)
    version = models.PositiveIntegerField()
    encrypted_information = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "actor", "version"], name="copy_information_version_once"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="copy_information_positive_version"
            ),
        ]


class RightsCopyInformationRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    information = models.ForeignKey(RightsCopyInformation, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    information_digest = models.CharField(max_length=64)
    policy_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField(null=True)
    original_mfa_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsCopyInformationReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    information = models.OneToOneField(RightsCopyInformation, on_delete=models.PROTECT)
    read = models.ForeignKey(RightsCopyInformationRead, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    information_digest = models.CharField(max_length=64)
    policy_digest = models.CharField(max_length=64)
    outcome = models.CharField(max_length=10)
    original_session_version = models.PositiveIntegerField(null=True)
    original_mfa_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_copy_information", "Independently review access information")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="copy_information_review_outcome",
            ),
        ]


class RightsExportInformationBinding(models.Model):
    export = models.OneToOneField(
        RightsExport, on_delete=models.PROTECT, related_name="information_binding"
    )
    review = models.ForeignKey(RightsCopyInformationReview, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    information_digest = models.CharField(max_length=64)
    policy_digest = models.CharField(max_length=64)
    inspection_digest = models.CharField(max_length=64)
    decision_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExportPortabilityBinding(models.Model):
    export = models.OneToOneField(
        RightsExport, on_delete=models.PROTECT, related_name="portability_binding"
    )
    review = models.ForeignKey("RightsPortabilitySelectionReview", on_delete=models.PROTECT)
    coverage_review = models.ForeignKey(
        "RightsPortabilityCoverageReview", on_delete=models.PROTECT, null=True
    )
    coverage_use = models.ForeignKey(
        RightsAction,
        on_delete=models.PROTECT,
        null=True,
        related_name="covered_portability_exports",
    )
    coverage_digest = models.CharField(max_length=64, default="")
    coverage_ciphertext_digest = models.CharField(max_length=64, default="")
    coverage_decision_digest = models.CharField(max_length=64, default="")
    coverage_reads_digest = models.CharField(max_length=64, default="")
    source_digest = models.CharField(max_length=64)
    selection_digest = models.CharField(max_length=64)
    ciphertext_digest = models.CharField(max_length=64)
    inspection_digest = models.CharField(max_length=64)
    decision_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsExportValidationSeal(models.Model):
    """Replay-provable equality of a full export validation's database inputs; no authority."""

    export = models.ForeignKey(RightsExport, on_delete=models.CASCADE, related_name="validation_seals")
    rule_version = models.CharField(max_length=64)
    caller_digest = models.CharField(max_length=64)
    encrypted_statements = models.TextField()
    result_digests = models.JSONField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["export", "rule_version", "caller_digest"])]


class RightsPortabilityAssessment(models.Model):
    request = models.ForeignKey(
        RightsRequest, on_delete=models.PROTECT, related_name="portability_assessments"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    encrypted_assessment = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "actor", "version"], name="portability_assessment_once"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="portability_assessment_positive"
            ),
        ]


class RightsPortabilityRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    assessment = models.ForeignKey(RightsPortabilityAssessment, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    assessment_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsPortabilityReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    assessment = models.OneToOneField(RightsPortabilityAssessment, on_delete=models.PROTECT)
    read = models.ForeignKey(RightsPortabilityRead, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    assessment_digest = models.CharField(max_length=64)
    outcome = models.CharField(max_length=10)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("review_portability", "Independently review portability assessments")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="portability_review_outcome",
            )
        ]


class RightsPortabilitySelection(models.Model):
    request = models.ForeignKey(
        RightsRequest, on_delete=models.PROTECT, related_name="portability_selections"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    assessment_review = models.ForeignKey(RightsPortabilityReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    assessment_digest = models.CharField(max_length=64)
    inspection_digest = models.CharField(max_length=64)
    decision_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    selection_digest = models.CharField(max_length=64)
    encrypted_selection = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "actor", "version"], name="portability_selection_once"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="portability_selection_positive"
            ),
        ]


class RightsPortabilitySelectionRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    selection = models.ForeignKey(RightsPortabilitySelection, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    selection_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    page_metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsPortabilitySelectionReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    selection = models.OneToOneField(RightsPortabilitySelection, on_delete=models.PROTECT)
    image_reads = models.JSONField(default=list)
    page_reads = models.JSONField(default=list)
    read = models.ForeignKey(RightsPortabilitySelectionRead, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    selection_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="portability_selection_review_outcome",
            ),
        ]


class RightsPortabilityImageRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    selection = models.ForeignKey(RightsPortabilitySelection, on_delete=models.PROTECT)
    selection_read = models.ForeignKey(RightsPortabilitySelectionRead, on_delete=models.PROTECT)
    photo = models.ForeignKey("mediafiles.Photo", on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    selection_digest = models.CharField(max_length=64)
    content_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsPortabilityCoverage(models.Model):
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    selection_review = models.ForeignKey(RightsPortabilitySelectionReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    selection_digest = models.CharField(max_length=64)
    coverage_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    encrypted_coverage = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "actor", "version"], name="portability_coverage_once"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="portability_coverage_positive"
            ),
        ]


class RightsPortabilityCoverageRead(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    coverage = models.ForeignKey(RightsPortabilityCoverage, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    coverage_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    dataset = models.CharField(max_length=40)
    row_index = models.PositiveIntegerField()
    field_page = models.PositiveIntegerField()
    binary = models.BooleanField(default=False)
    page_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(field_page__gte=1), name="portability_coverage_read_page"
            ),
        ]


class RightsPortabilityCoverageReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    coverage = models.OneToOneField(RightsPortabilityCoverage, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    coverage_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    read_ids = models.JSONField(default=list)
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="portability_coverage_review_outcome",
            )
        ]


class RightsPortabilityResponseDraft(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT)
    coverage_review = models.ForeignKey(RightsPortabilityCoverageReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    response_version = models.PositiveIntegerField()
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    export_digest = models.CharField(max_length=64)
    coverage_digest = models.CharField(max_length=64)
    text_digest = models.CharField(max_length=64)
    encrypted_response = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsPortabilityResponseReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    draft = models.OneToOneField(RightsPortabilityResponseDraft, on_delete=models.PROTECT)
    read_action = models.ForeignKey(
        RightsAction, on_delete=models.PROTECT, related_name="final_response_reviews"
    )
    text_digest = models.CharField(max_length=64)
    ciphertext_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="portability_response_review_outcome",
            )
        ]


class RightsPortabilityClosure(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    review = models.OneToOneField(RightsPortabilityResponseReview, on_delete=models.PROTECT)
    closed_case_version = models.PositiveIntegerField()
    closed_response_version = models.PositiveIntegerField()
    channel_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecoveryOutbox(models.Model):
    """Transactional execution receipt; independent export remains required."""

    id = models.BigAutoField(primary_key=True)
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    execution = models.OneToOneField(ErasureExecution, on_delete=models.PROTECT)
    sequence = models.PositiveBigIntegerField(null=True, unique=True)
    encoded_record = models.JSONField(null=True)
    encrypted_event = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    exported_at = models.DateTimeField(null=True)


class RecoveryLedgerState(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    ledger_id = models.UUIDField(default=uuid.uuid4, unique=True)
    sequence = models.PositiveBigIntegerField(default=0)
    head = models.CharField(max_length=64, default="0" * 64)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="recovery_ledger_singleton")
        ]


class RecoveryApplication(models.Model):
    execution_id = models.UUIDField(primary_key=True)
    scope = models.CharField(max_length=12)
    subject_reference = models.CharField(max_length=64)
    receipt_digest = models.CharField(max_length=64)
    encrypted_receipt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecoveryMediaJob(models.Model):
    application = models.ForeignKey(RecoveryApplication, on_delete=models.PROTECT)
    blob = models.ForeignKey("mediafiles.Blob", null=True, on_delete=models.PROTECT)
    blob_reference = models.UUIDField()
    encrypted_paths = models.TextField()
    status = models.CharField(max_length=12, default="queued")
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "blob_reference"],
                name="one_recovery_media_job_per_operation_blob",
            )
        ]


class RightsAccessResponseDraft(models.Model):
    coverage_review = models.ForeignKey(
        "RightsAccessCoverageReview", null=True, on_delete=models.PROTECT
    )
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT)
    information_review = models.ForeignKey(RightsCopyInformationReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    response_version = models.PositiveIntegerField()
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    export_digest = models.CharField(max_length=64)
    binding_digest = models.CharField(max_length=64)
    text_digest = models.CharField(max_length=64)
    encrypted_response = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsAccessResponseReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    draft = models.OneToOneField(RightsAccessResponseDraft, on_delete=models.PROTECT)
    read_action = models.ForeignKey(
        RightsAction, on_delete=models.PROTECT, related_name="access_final_response_reviews"
    )
    text_digest = models.CharField(max_length=64)
    ciphertext_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="access_response_review_outcome",
            )
        ]


class RightsAccessCoverage(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    export = models.ForeignKey(RightsExport, on_delete=models.PROTECT)
    information_review = models.ForeignKey(RightsCopyInformationReview, on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    response_version = models.PositiveIntegerField()
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    export_digest = models.CharField(max_length=64)
    binding_digest = models.CharField(max_length=64)
    accounting_digest = models.CharField(max_length=64)
    encrypted_coverage = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsAccessCoverageReview(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    coverage = models.OneToOneField(RightsAccessCoverage, on_delete=models.PROTECT)
    read_action = models.ForeignKey(
        RightsAction, on_delete=models.PROTECT, related_name="access_coverage_reviews"
    )
    accounting_digest = models.CharField(max_length=64)
    ciphertext_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    outcome = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["approved", "rejected"]),
                name="access_coverage_review_outcome",
            )
        ]


class RightsAccessScopeInventory(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT)
    proof = models.ForeignKey(RightsProof, on_delete=models.PROTECT)
    case_version = models.PositiveIntegerField()
    response_version = models.PositiveIntegerField()
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    encrypted_inventory = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RightsAccessFieldDecision(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    inventory = models.ForeignKey(RightsAccessScopeInventory, on_delete=models.PROTECT)
    read_action = models.ForeignKey(
        RightsAction, on_delete=models.PROTECT, related_name="access_field_decisions"
    )
    encrypted_body = models.TextField()
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True)
    review_action = models.OneToOneField(
        RightsAction, null=True, on_delete=models.PROTECT, related_name="access_field_review"
    )
    outcome = models.CharField(max_length=10, default="pending")
    review_read_action = models.ForeignKey(
        RightsAction, null=True, on_delete=models.PROTECT, related_name="access_field_review_reads"
    )
    reviewer_session_version = models.PositiveIntegerField(null=True)
    reviewer_mfa_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["pending", "approved", "rejected"]),
                name="access_field_decision_outcome",
            )
        ]


class RightsAccessClosure(models.Model):
    action = models.OneToOneField(RightsAction, on_delete=models.PROTECT)
    response = models.OneToOneField(RightsResponse, on_delete=models.PROTECT)
    review = models.OneToOneField(RightsAccessResponseReview, on_delete=models.PROTECT)
    closed_case_version = models.PositiveIntegerField()
    closed_response_version = models.PositiveIntegerField()
    channel_digest = models.CharField(max_length=64)
    original_session_version = models.PositiveIntegerField()
    original_mfa_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RightsRecipientNotice(models.Model):
    """Minimal private notice of one execution to one currently authorized account."""

    request = models.ForeignKey(RightsRequest, on_delete=models.PROTECT)
    action = models.ForeignKey(RightsAction, on_delete=models.PROTECT)
    execution_key = models.CharField(max_length=36)
    recipient = models.ForeignKey("core.User", on_delete=models.PROTECT)
    authorization_version = models.CharField(max_length=30)
    encrypted_payload = models.TextField()
    payload_digest = models.CharField(max_length=64)
    acknowledged_at = models.DateTimeField(null=True)
    acknowledged_read = models.ForeignKey(
        RightsAction, null=True, on_delete=models.PROTECT, related_name="recipient_notice_acks"
    )
    acknowledged_action = models.ForeignKey(
        RightsAction,
        null=True,
        on_delete=models.PROTECT,
        related_name="recipient_notice_ack_actions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "execution_key", "recipient", "authorization_version"],
                name="rights_recipient_execution_once",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        acknowledged_at__isnull=True,
                        acknowledged_read__isnull=True,
                        acknowledged_action__isnull=True,
                    )
                    | models.Q(
                        acknowledged_at__isnull=False,
                        acknowledged_read__isnull=False,
                        acknowledged_action__isnull=False,
                    )
                ),
                name="rights_recipient_ack_has_read",
            ),
        ]

# Kept separate to make the immutable metadata's scope explicit.
from .evidence_chain_models import RightsEvidenceEvent, RightsEvidenceHead  # noqa: E402,F401
