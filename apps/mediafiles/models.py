import uuid

from django.db import models
from django.utils import timezone


class Blob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sha256 = models.CharField(max_length=64, unique=True)
    original = models.FileField(upload_to="originals/", blank=True)
    derivative = models.FileField(upload_to="derivatives/", blank=True)
    status = models.CharField(max_length=12, default="queued")
    phash = models.CharField(max_length=16, blank=True, db_index=True)
    signature = models.JSONField(default=dict)
    regional_hashes = models.JSONField(default=list)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True)
    error_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision = models.ForeignKey(
        "listings.Revision", on_delete=models.CASCADE, related_name="photos"
    )
    blob = models.ForeignKey(Blob, on_delete=models.PROTECT, related_name="photos")
    position = models.PositiveSmallIntegerField(default=0)
    approved = models.BooleanField(default=False)
    comparison_complete = models.BooleanField(default=False)
    removed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "blob"],
                condition=models.Q(removed_at__isnull=True),
                name="one_blob_per_revision",
            )
        ]


class Match(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="matches")
    candidate = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="matched_by")
    method = models.CharField(max_length=16)
    score = models.FloatField(default=1)
    resolved_at = models.DateTimeField(null=True)
    decision = models.CharField(max_length=16, blank=True)
    review_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["photo", "candidate"], name="photo_candidate_once")
        ]


class UploadAttempt(models.Model):
    user = models.ForeignKey("core.User", on_delete=models.CASCADE)
    revision = models.ForeignKey("listings.Revision", on_delete=models.CASCADE)
    result = models.CharField(max_length=24)
    created_at = models.DateTimeField(auto_now_add=True)


class MatchResolution(models.Model):
    match = models.ForeignKey(Match, on_delete=models.PROTECT, related_name="resolutions")
    reviewer = models.ForeignKey("core.User", on_delete=models.PROTECT)
    outcome = models.CharField(max_length=16)
    reason = models.CharField(max_length=1000)
    evidence_reference = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)


class PhotoRestriction(models.Model):
    person = models.ForeignKey(
        "core.Person", on_delete=models.PROTECT, related_name="photo_restrictions"
    )
    manager_version = models.PositiveIntegerField()
    photo = models.ForeignKey(Photo, on_delete=models.PROTECT, related_name="restrictions")
    decision = models.ForeignKey(
        MatchResolution, on_delete=models.PROTECT, related_name="restrictions"
    )
    reason_code = models.CharField(max_length=40, default="shared_photo_conflict")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "decision"], name="one_photo_restriction_per_person_decision"
            )
        ]


class PhotoAppeal(models.Model):
    restriction = models.OneToOneField(
        PhotoRestriction, on_delete=models.PROTECT, related_name="appeal"
    )
    actor = models.ForeignKey("core.User", on_delete=models.PROTECT, related_name="photo_appeals")
    review_version = models.PositiveIntegerField()
    explanation = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, default="open")
    reviewer = models.ForeignKey(
        "core.User", null=True, on_delete=models.PROTECT, related_name="photo_appeals_reviewed"
    )
    result = models.CharField(max_length=12, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)


class MediaErasure(models.Model):
    blob = models.OneToOneField(Blob, on_delete=models.PROTECT, related_name="erasure")
    execution = models.ForeignKey(
        "safety.ErasureExecution", on_delete=models.PROTECT, related_name="media_jobs"
    )
    encrypted_paths = models.TextField()
    status = models.CharField(max_length=12, default="queued", db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True)
    error_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
