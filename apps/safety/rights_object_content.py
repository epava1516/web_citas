"""Dual-reader binary export storage; original Fernet rows remain readable."""

import io

from botocore.exceptions import ClientError
from cryptography.fernet import InvalidToken
from django.conf import settings

from .crypto import cipher
from .object_storage.codec import InvalidObject
from .object_storage.factory import repository
from .object_storage.repository import PREFIX


def context(export_id, kind, identifier):
    if kind not in {"image", "part"}:
        raise ValueError("Unsupported export object kind")
    return f"rights-export/v1/{export_id}/{kind}/{identifier}".encode("ascii")


def seal_binary(content, export_id, kind, identifier):
    if not settings.RIGHTS_OBJECT_STORAGE_ENABLED:
        return cipher().encrypt(content).decode()
    return repository().write(io.BytesIO(content), context(export_id, kind, identifier))


def unseal_binary(value, export_id, kind, identifier):
    if not value.startswith(PREFIX):
        return cipher().decrypt(value.encode())
    output = io.BytesIO()
    try:
        repository().read(value, output, context(export_id, kind, identifier))
    except (InvalidObject, ClientError) as error:
        raise InvalidToken from error
    return output.getvalue()


def image_bytes(row):
    return unseal_binary(row.encrypted_content, row.export_id, "image", row.photo_id)


def part_bytes(row):
    return unseal_binary(row.encrypted_content, row.export_id, "part", row.position)


def purge_export_objects(exports):
    """Physical delete precedes SQL ref clearing; tombstones prevent restore replay."""
    from .models import RightsExportImage, RightsExportPart
    from .rights_object_delivery import purge_export_deliveries

    purge_export_deliveries(exports)
    repo = None
    for model in (RightsExportImage, RightsExportPart):
        refs = model.objects.filter(export__in=exports, encrypted_content__startswith=PREFIX)
        for value in refs.values_list("encrypted_content", flat=True).iterator(chunk_size=100):
            if repo is None:
                repo = repository()
            repo.purge(value)


def verify_export_objects(export):
    """Mandatory physical guard before a DB validation seal may be trusted.

    Signed refs and SQL equality do not prove externally retained bytes unchanged.
    Each object verifies its purge tombstone, digest, complete AEAD and owner context.
    """
    from django.core.exceptions import ValidationError

    from .models import RightsExportImage, RightsExportPart

    try:
        for row in RightsExportImage.objects.filter(
            export=export, encrypted_content__startswith=PREFIX
        ).iterator(chunk_size=1):
            image_bytes(row)
        for row in RightsExportPart.objects.filter(
            export=export, encrypted_content__startswith=PREFIX
        ).iterator(chunk_size=1):
            part_bytes(row)
    except (InvalidToken, OSError) as error:
        raise ValidationError("External export object unavailable or changed") from error


from celery import shared_task  # noqa: E402


@shared_task
def purge_orphan_export_objects():
    """Remove aborted-generation objects after one day; tombstones remain durable.

    Export generation is bounded well below the grace interval. Freeze writes in
    recovery; retained tombstones are a separate recovery authority, not a backup.
    """
    from datetime import timedelta

    from django.utils import timezone

    from .models import RightsExportImage, RightsExportPart

    if not settings.RIGHTS_OBJECT_STORAGE_ENABLED or settings.RECOVERY_MODE:
        return 0
    repo, live = repository(), set()
    for model in (RightsExportImage, RightsExportPart):
        for reference in (
            model.objects.filter(encrypted_content__startswith=PREFIX)
            .values_list("encrypted_content", flat=True)
            .iterator(chunk_size=100)
        ):
            live.add(repo.descriptor(reference)["key"])
    cutoff, deleted = timezone.now() - timedelta(days=1), 0
    for page in repo.client.get_paginator("list_objects_v2").paginate(
        Bucket=repo.bucket, Prefix="encrypted/v1/"
    ):
        for item in page.get("Contents", []):
            if item["Key"] not in live and item["LastModified"] < cutoff:
                # No reference ever committed; unlike a released artifact, no replay authority.
                repo.delete_unreferenced(item["Key"])
                deleted += 1
    return deleted
