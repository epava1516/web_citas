import uuid

from django.db import models


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
