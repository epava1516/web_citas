"""Bounded ZIP packages for already reviewed, sanitized image snapshots.

This builder grants no access and does not decide which images may be delivered.
Callers must pass authorized snapshot bytes, never storage paths or original names.
"""

import io
import uuid
import zipfile

from django.core.exceptions import ValidationError

PART_LIMIT = 64 * 1024 * 1024
IMAGE_LIMIT = 10 * 1024 * 1024


def packages(snapshots, limit=PART_LIMIT):
    """Yield bounded stored ZIPs with UUID-only filenames and deterministic metadata."""
    if not 22 < limit <= PART_LIMIT:
        raise ValidationError("Invalid package size")
    seen = set()
    pending = []
    size = 22  # End of central directory, no comment.
    for attachment, content in snapshots:
        try:
            identifier = str(uuid.UUID(str(attachment)))
        except (ValueError, TypeError, AttributeError) as error:
            raise ValidationError("Invalid attachment identifier") from error
        if identifier in seen:
            raise ValidationError("Duplicate attachment")
        seen.add(identifier)
        if not isinstance(content, bytes) or not content or len(content) > IMAGE_LIMIT:
            raise ValidationError("Invalid sanitized snapshot size")
        name = identifier + ".webp"
        contribution = len(content) + 76 + 2 * len(name.encode("ascii"))
        if contribution + 22 > limit:
            raise ValidationError("Attachment exceeds package limit")
        if pending and size + contribution > limit:
            yield archive(pending, limit)
            pending = []
            size = 22
        pending.append((identifier, name, content))
        size += contribution
    if pending:
        yield archive(pending, limit)


def archive(items, limit):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as package:
        for _, name, content in items:
            metadata = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            metadata.external_attr = 0o600 << 16
            package.writestr(metadata, content)
    content = output.getvalue()
    if len(content) > limit:
        raise ValidationError("Package exceeds size limit")
    return {"attachments": [item[0] for item in items], "content": content}
