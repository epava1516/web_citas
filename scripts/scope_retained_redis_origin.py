"""Bind an existing partial encrypted AOF capture to a private inventory slot.

Operator-only preparation, not authorization or proof of exhaustive history.
Does not contact Redis, replay commands, or replace existing origin files.
"""

import argparse
import base64
import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import UUID

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from apps.safety.redis_retained_history import MAX_BYTES
from scripts.collect_access_resource_logs import write_bundle


@sensitive_variables()
def scoped_body(body, inventory):
    common = {"schema", "project", "captured_at", "sha256", "content_base64", "partial"}
    if (
        set(body) != common
        or body["schema"] != "local-redis-aof-origin-v1"
        or body["project"] != "web-modelos"
        or body["partial"] is not True
    ):
        raise ValueError("Exact partial retained AOF origin required")
    captured = datetime.fromisoformat(body["captured_at"])
    if captured.tzinfo is None or captured > inventory.created_at:
        raise ValueError("Origin outside inventory cutoff")
    raw = base64.b64decode(body["content_base64"], validate=True)
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != body["sha256"]:
        raise ValueError("Retained AOF content changed")
    return body | {
        "schema": "local-redis-aof-scoped-origin-v1",
        "request": str(inventory.request_id),
        "inventory": inventory.pk,
        "source_digest": inventory.source_digest,
        "cutoff": inventory.created_at.isoformat(),
    }


@sensitive_variables()
def read_origin(path):
    from apps.safety.rights_access_response_draft import checked_body

    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) & 0o077
            or before.st_size > 128 * 1024 * 1024
        ):
            raise ValueError("Owned private bounded encrypted origin required")
        encrypted = stream.read(128 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
        def identity(row):
            return (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
        if (
            len(encrypted) != before.st_size
            or identity(before) != identity(after)
            or identity(after) != identity(Path(path).lstat())
        ):
            raise ValueError("Retained origin changed during preparation")
    return checked_body(encrypted.decode())


def prepare_origin(path, directory, inventory):
    return write_bundle(
        directory,
        scoped_body(read_origin(path), inventory),
        case_id=inventory.request_id,
        inventory_id=inventory.pk,
        kind="redis-history",
    )


def prepare_origins(paths, directory, inventory, *, decoder=None, decoder_sha256=None, aux_decoder=None, aux_decoder_sha256=None):
    from apps.safety.retained_redis_origins import checked_origin

    if not 1 <= len(paths) <= 16:
        raise ValueError("Bounded retained origins required")
    bodies = [read_origin(path) for path in paths]
    if any(not isinstance(body, dict) for body in bodies):
        raise ValueError("Retained origin object required")
    if len(bodies) == 1 and bodies[0].get("schema") == "local-redis-aof-origin-v1":
        return write_bundle(
            directory, scoped_body(bodies[0], inventory),
            case_id=inventory.request_id, inventory_id=inventory.pk, kind="redis-history",
        )
    origins, identities, total = [], set(), 0
    for body in bodies:
        if isinstance(body, dict) and body.get("schema") == "local-redis-aof-origin-v1":
            origin = body
        else:
            if decoder is None or decoder_sha256 is None:
                raise ValueError("Pinned operator decoder required for RDB")
            from scripts.decode_retained_rdb_origin import decode_body

            origin = decode_body(body, decoder, decoder_sha256=decoder_sha256)
            if aux_decoder is not None or aux_decoder_sha256 is not None:
                if aux_decoder is None or aux_decoder_sha256 is None:
                    raise ValueError("AUX collector and verified hash required together")
                from scripts.collect_retained_rdb_aux import collect_aux

                origin = collect_aux(body, origin, aux_decoder, decoder_sha256=aux_decoder_sha256)
        raw, kind, identity = checked_origin(origin, inventory.created_at)
        if (kind, identity) in identities:
            raise ValueError("Duplicate retained physical origin")
        identities.add((kind, identity))
        total += len(raw)
        if "aux_metadata" in origin:
            from apps.safety.rights_exports import canonical

            total += len(canonical(origin["aux_metadata"]).encode())
        if total > MAX_BYTES:
            raise ValueError("Retained origin aggregate byte limit")
        origins.append(origin)
    body = {
        "schema": "local-redis-retained-origins-scoped-v1", "project": "web-modelos",
        "request": str(inventory.request_id), "inventory": inventory.pk,
        "source_digest": inventory.source_digest, "cutoff": inventory.created_at.isoformat(),
        "origins": origins, "partial": True,
    }
    return write_bundle(
        directory, body, case_id=inventory.request_id, inventory_id=inventory.pk,
        kind="redis-history",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", type=Path, action="append", required=True)
    parser.add_argument("--decoder", type=Path)
    parser.add_argument("--decoder-sha256")
    parser.add_argument("--aux-decoder", type=Path)
    parser.add_argument("--aux-decoder-sha256")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--request", type=UUID, required=True)
    parser.add_argument("--inventory", type=int, required=True)
    args = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.utils import timezone

    from apps.safety.models import RightsAccessScopeInventory

    try:
        inventory = RightsAccessScopeInventory.objects.get(
            pk=args.inventory, request_id=args.request, purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        path = prepare_origins(
            args.origin, args.output_directory, inventory,
            decoder=args.decoder, decoder_sha256=args.decoder_sha256,
            aux_decoder=args.aux_decoder, aux_decoder_sha256=args.aux_decoder_sha256,
        )
    except (OSError, ValueError, TypeError, KeyError, ValidationError, subprocess.SubprocessError, RightsAccessScopeInventory.DoesNotExist):
        parser.error("Retained origin or inventory unavailable; no accepted artifact")
    print(json.dumps({"encrypted_artifact": str(path), "partial": True, "coverage_accepted": False}))


if __name__ == "__main__":
    main()
