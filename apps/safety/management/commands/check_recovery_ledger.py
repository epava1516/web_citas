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

    def handle(self, *args, **options):
        try:
            encryption = os.environ["RECOVERY_ENCRYPTION_KEY"].encode("ascii")
            signing = base64.b64decode(
                os.environ["RECOVERY_SIGNING_KEY"], altchars=b"-_", validate=True
            )
            codec = RecoveryLedger(encryption, signing)
            start = Checkpoint(
                options["backup_ledger"], options["backup_sequence"], options["backup_head"]
            )
            store = RecoveryStore(
                options["records_directory"], options["checkpoint_directory"], codec
            )
            receipts = store.recover(start)
            with transaction.atomic():
                for receipt in receipts:
                    validate_ownership(receipt)
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
