"""Transient proxy grants, tied to the existing audited download."""

import uuid

from django.db import models


class RightsObjectDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    download = models.OneToOneField("safety.RightsExportDownload", on_delete=models.PROTECT)
    generation = models.CharField(max_length=64)
    object_name = models.CharField(max_length=32, unique=True)
    content_sha256 = models.CharField(max_length=64)
    content_bytes = models.PositiveIntegerField()
    content_type = models.CharField(max_length=64)
    filename = models.CharField(max_length=80)
    binding_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True)
    purged_at = models.DateTimeField(null=True)

    class Meta:
        app_label = "safety"
