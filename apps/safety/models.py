import uuid

from django.db import models


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
