"""Explicit local administrative snapshot; no scheduler or network delivery."""
import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.operational_snapshot import SnapshotUnavailable, collect_snapshot


class Command(BaseCommand):
    help = "Print aggregate durable work counters; does not certify worker or broker health"
    requires_system_checks = []

    def handle(self, *args, **options):
        try:
            snapshot = collect_snapshot()
        except SnapshotUnavailable as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(snapshot, sort_keys=True, allow_nan=False))
