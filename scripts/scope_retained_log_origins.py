"""Bind selected existing encrypted log captures to an immutable inventory slot.

Operator-only preparation; no Docker access, send, erasure or coverage acceptance.
"""

import argparse
import hashlib
import os
from pathlib import Path
from uuid import UUID

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from scripts.collect_access_resource_logs import write_bundle
from scripts.inventory_retained_origins import inspect_origin
from scripts.scope_retained_redis_origin import read_origin


@sensitive_variables()
def prepare_origins(paths, directory, inventory):
    from types import SimpleNamespace

    from apps.safety.retained_log_origins import (
        MAX_CAPTURES,
        MAX_CONTENT_BYTES,
        PROJECT,
        checked_capture,
        checked_scoped_captures,
    )
    from apps.safety.rights_exports import canonical

    if not 1 <= len(paths) <= MAX_CAPTURES:
        raise ValueError("Bounded explicit capture selection required")
    origins, total = [], 0
    for path in paths:
        before = inspect_origin(path)
        capture = read_origin(path)
        total += checked_capture(capture, inventory.created_at)
        if total > MAX_CONTENT_BYTES:
            raise ValueError("Historical capture aggregate byte limit")
        if before != inspect_origin(path):
            raise ValueError("Historical capture changed during preparation")
        origins.append(
            {
                "capture": capture,
                "capture_sha256": hashlib.sha256(canonical(capture).encode()).hexdigest(),
                "ciphertext_sha256": before["sha256"],
            }
        )
    body = {
        "schema": "local-log-retained-origins-scoped-v1",
        "project": PROJECT,
        "request": str(inventory.request_id),
        "inventory": inventory.pk,
        "source_digest": inventory.source_digest,
        "cutoff": inventory.created_at.isoformat(),
        "origins": origins,
        "partial": True,
    }
    checked_scoped_captures(
        body, SimpleNamespace(pk=inventory.request_id), inventory, inventory.created_at
    )
    return write_bundle(directory, body, case_id=inventory.request_id, inventory_id=inventory.pk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", type=Path, action="append", required=True)
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
        path = prepare_origins(args.origin, args.output_directory, inventory)
    except (OSError, ValueError, TypeError, KeyError, ValidationError, RightsAccessScopeInventory.DoesNotExist):
        parser.error("Retained log origin or inventory unavailable; no accepted artifact")
    print(path)


if __name__ == "__main__":
    main()
