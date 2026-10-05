"""Bounded transport fragments of already authorized JSON, without scope decisions."""

import hashlib
import io
import json
import zipfile
from itertools import chain

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

DATA_PART_LIMIT = 8 * 1024 * 1024
MAX_PART_LIMIT = 64 * 1024 * 1024


def _archive(fragment, position, limit):
    name = f"data-{position:08d}.json.fragment"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as package:
        metadata = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        metadata.external_attr = 0o600 << 16
        package.writestr(metadata, fragment)
    zipped = output.getvalue()
    if len(zipped) > limit:
        raise ValidationError("Data package exceeds size limit")
    return {
        "position": position,
        "filename": name,
        "size": len(fragment),
        "sha256": hashlib.sha256(fragment).hexdigest(),
        "content": zipped,
    }


@sensitive_variables()
def chunk_packages(chunks, summary, limit=DATA_PART_LIMIT):
    """Consume bytes incrementally; summary is complete only after iterator exhaustion."""
    if type(limit) is not int or not 256 <= limit <= MAX_PART_LIMIT:
        raise ValidationError("Invalid data package size")
    position = 1
    pending = bytearray()
    digest = hashlib.sha256()
    total = 0
    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise ValidationError("Invalid data fragment")
        digest.update(chunk)
        total += len(chunk)
        offset = 0
        while offset < len(chunk):
            name = f"data-{position:08d}.json.fragment"
            capacity = limit - 98 - 2 * len(name)
            count = min(capacity - len(pending), len(chunk) - offset)
            pending.extend(chunk[offset : offset + count])
            offset += count
            if len(pending) == capacity:
                yield _archive(bytes(pending), position, limit)
                pending.clear()
                position += 1
    if pending:
        yield _archive(bytes(pending), position, limit)
    if not total:
        raise ValidationError("Empty data document")
    summary.update(size=total, sha256=digest.hexdigest())


@sensitive_variables()
def data_packages(content, limit=DATA_PART_LIMIT):
    """Concatenate numbered fragment bytes before decoding UTF-8 or parsing JSON."""
    if not isinstance(content, bytes) or not content:
        raise ValidationError("Invalid data package")
    yield from chunk_packages(iter([content]), {}, limit=limit)


@sensitive_variables()
def json_chunks(value):
    """Encode JSON incrementally; an individual encoder string may still be large."""
    for text in json.JSONEncoder(ensure_ascii=False, sort_keys=True).iterencode(value):
        for start in range(0, len(text), 16384):
            yield text[start : start + 16384].encode("utf-8")


@sensitive_variables()
def stored_payload(export, reviewed):
    """Called inside export generation's transaction; all fragments share its authority."""
    from .crypto import cipher, seal
    from .models import RightsExportPart

    encoded = iter(json_chunks(reviewed))
    prefix = bytearray()
    for chunk in encoded:
        prefix.extend(chunk)
        if len(prefix) > DATA_PART_LIMIT:
            break
    else:
        return seal(reviewed)
    summary = {}
    image_parts = reviewed.get("parts", [])
    manifest = {
        "schema": "rights-data-manifest-v1",
        "document_schema": reviewed["schema"],
        "partial": reviewed["partial"],
        "simulation": reviewed["simulation"],
        "pending_review": reviewed["pending_review"],
        "encoding": "utf-8",
        "parts": image_parts,
        "data_parts": [],
    }
    for package in chunk_packages(chain([bytes(prefix)], encoded), summary, limit=DATA_PART_LIMIT):
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
    manifest.update(summary)
    return seal(manifest)
