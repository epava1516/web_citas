"""Apply verified recovery effects offline; never enable public exposure."""

import json

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection

from apps.safety.models import RecoveryMediaJob
from apps.safety.recovery_apply import reconcile
from apps.safety.recovery_media import destroy_due

from .check_recovery_ledger import Command as PreflightCommand


class Command(PreflightCommand):
    help = "Reconcile verified recovery effects in isolated mode; never reopen the site"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--media-limit", type=int, default=100)

    def handle(self, *args, **options):
        if not settings.RECOVERY_MODE or connection.in_atomic_block:
            raise CommandError("Explicit isolated recovery mode and no outer transaction required")
        limit = options["media_limit"]
        if type(limit) is not int or not 1 <= limit <= 100:
            raise CommandError("Media limit must be between1 and100")
        try:
            store, start = self.recovery_store(options)
            result = reconcile(store, start)
            completed = destroy_due(store, start, limit=limit)
        except (ValueError, KeyError, OSError, TypeError) as error:
            # Database effects may already be committed, and physical deletion is
            # irreversible. Keep isolation and retry against the same authority.
            raise CommandError(
                "Recovery failed; keep isolated and inspect private audit"
            ) from error
        pending = RecoveryMediaJob.objects.exclude(status="completed")
        result.update(
            media_completed=completed,
            pending_media_jobs=pending.count(),
            exhausted_media_jobs=pending.filter(attempts__gte=5).count(),
            publication_authorized=False,
        )
        self.stdout.write(json.dumps(result))
