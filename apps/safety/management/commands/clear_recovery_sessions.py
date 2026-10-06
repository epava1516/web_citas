"""Invalidate and destroy all restored DB sessions after verified reconciliation."""

import json

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.base import CommandError
from django.db import transaction

from apps.safety.crypto import unseal
from apps.safety.models import RecoveryApplication
from scripts.recovery_ledger import digest
from scripts.recovery_receipts import validate_receipt

from .check_recovery_ledger import Command as PreflightCommand


class Command(PreflightCommand):
    help = "Delete all sessions in the isolated recovery DB after verified reconciliation"

    def handle(self, *args, **options):
        if (
            not settings.RECOVERY_MODE
            or settings.SESSION_ENGINE != "django.contrib.sessions.backends.db"
        ):
            raise CommandError("Isolated recovery with database sessions required")
        try:
            store, start = self.recovery_store(options)
            receipts = store.recover(start)
            with transaction.atomic():
                for receipt in receipts:
                    validate_receipt(receipt)
                    application = (
                        RecoveryApplication.objects.select_for_update()
                        .filter(pk=receipt["execution"])
                        .first()
                    )
                    if not application or (
                        application.receipt_digest != digest(receipt)
                        or application.scope != receipt["scope"]
                        or application.subject_reference != receipt["subject"]
                        or unseal(application.encrypted_receipt) != receipt
                    ):
                        raise ValueError("Recovery reconciliation not verified")
                # This is an explicit global recovery operation, not individual erasure.
                # Only the configured isolated database is touched; session contents
                # are never decoded, selected for logs, or returned as evidence.
                deleted, _ = Session.objects.all().delete()
        except (InvalidToken, ValueError, KeyError, OSError, TypeError) as error:
            raise CommandError("Session recovery failed; keep isolated") from error
        self.stdout.write(
            json.dumps(
                {
                    "sessions_deleted": deleted,
                    "publication_authorized": False,
                }
            )
        )
