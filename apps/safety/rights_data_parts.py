"""Bounded transport fragments of already authorized JSON, without scope decisions."""

import hashlib
import io
import zipfile

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

DATA_PART_LIMIT = 8 * 1024 * 1024
MAX_PART_LIMIT = 64 * 1024 * 1024


@sensitive_variables()
def data_packages(content, limit=DATA_PART_LIMIT):
    """Concatenate numbered fragment bytes before decoding UTF-8 or parsing JSON."""
    if not isinstance(content, bytes) or not content or not 256 <= limit <= MAX_PART_LIMIT:
        raise ValidationError("Invalid data package")
    position = 1
    offset = 0
    while offset < len(content):
        name = f"data-{position:08d}.json.fragment"
        # Stored ZIP: local header + central entry + filename twice + end record.
        capacity = limit - 98 - 2 * len(name.encode("ascii"))
        fragment = content[offset : offset + capacity]
        output = io.BytesIO()
        with zipfile.ZipFile(
            output, "w", compression=zipfile.ZIP_STORED, allowZip64=False
        ) as package:
            metadata = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            metadata.external_attr = 0o600 << 16
            package.writestr(metadata, fragment)
        zipped = output.getvalue()
        if len(zipped) > limit:
            raise ValidationError("Data package exceeds size limit")
        yield {
            "position": position,
            "filename": name,
            "size": len(fragment),
            "sha256": hashlib.sha256(fragment).hexdigest(),
            "content": zipped,
        }
        offset += len(fragment)
        position += 1


@sensitive_variables()
def stored_payload(export, reviewed):
    """Called inside export generation's transaction; all fragments share its authority."""
    import json

    from .crypto import cipher, seal
    from .models import RightsExportPart

    content = json.dumps(reviewed, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(content) <= DATA_PART_LIMIT:
        return seal(reviewed)
    image_parts = reviewed.get("parts", [])
    manifest = {
        "schema": "rights-data-manifest-v1",
        "document_schema": reviewed["schema"],
        "partial": reviewed["partial"],
        "simulation": reviewed["simulation"],
        "pending_review": reviewed["pending_review"],
        "encoding": "utf-8",
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "parts": image_parts,
        "data_parts": [],
    }
    for package in data_packages(content, limit=DATA_PART_LIMIT):
        part = RightsExportPart.objects.create(
            export=export,
            position=len(image_parts) + package["position"],
            attachments=[],
            encrypted_content=cipher().encrypt(package["content"]).decode(),
        )
        manifest["data_parts"].append(
            {
                "id": str(part.pk),
                "position": part.position,
                "fragment_position": package["position"],
                "filename": package["filename"],
                "size": package["size"],
                "sha256": package["sha256"],
            }
        )
    return seal(manifest)
