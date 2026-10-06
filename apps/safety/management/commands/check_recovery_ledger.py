"""Non-mutating recovery preflight; never an authorization to reopen exposure."""

import base64
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.safety.recovery_ownership import validate_ownership
from scripts.recovery_ledger import Checkpoint, RecoveryLedger
from scripts.recovery_store import RecoveryStore


class Command(BaseCommand):
    help = "Verify recovery chain and resource ownership; does not apply effects or reopen the site"

    def add_arguments(self, parser):
        parser.add_argument("--records-directory", required=True)
        parser.add_argument("--checkpoint-directory", required=True)
        parser.add_argument("--backup-ledger", required=True)
        parser.add_argument("--backup-sequence", required=True, type=int)
        parser.add_argument("--backup-head", required=True)
        parser.add_argument("--expected-ledger", required=True)
        parser.add_argument("--expected-sequence", required=True, type=int)
        parser.add_argument("--expected-head", required=True)

    def recovery_store(self, options):
        encryption = os.environ["RECOVERY_ENCRYPTION_KEY"].encode("ascii")
        signing = base64.b64decode(
            os.environ["RECOVERY_SIGNING_KEY"], altchars=b"-_", validate=True
        )
        codec = RecoveryLedger(encryption, signing)
        start = Checkpoint(
            options["backup_ledger"], options["backup_sequence"], options["backup_head"]
        )
        expected = Checkpoint(
            options["expected_ledger"], options["expected_sequence"], options["expected_head"]
        )
        return RecoveryStore(
            options["records_directory"],
            options["checkpoint_directory"],
            codec,
            expected_checkpoint=expected,
        ), start

    def handle(self, *args, **options):
        try:
            store, start = self.recovery_store(options)
            receipts = store.recover(start)
            with transaction.atomic():
                projected_photo_blobs = {}
                for receipt in receipts:
                    validate_ownership(receipt, projected_photo_blobs=projected_photo_blobs)
                    for photo in receipt["references"]["resources"].get("photos", []):
                        if "replacement" in photo:
                            projected_photo_blobs[photo["photo"]] = photo["replacement"]
        except (ValueError, KeyError, OSError, TypeError) as error:
            raise CommandError("Recovery preflight failed; keep recovery isolated") from error
        self.stdout.write(
            json.dumps(
                {
                    "preflight_verified": True,
                    "events_checked": len(receipts),
                    "effects_applied": False,
                    "publication_authorized": False,
                }
            )
        )
