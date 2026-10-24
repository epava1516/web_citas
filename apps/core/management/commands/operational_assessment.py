"""Explicit read-only administrative assessment; fixed responses, no remediation."""
import json
import time

from django.core.management.base import BaseCommand, CommandError

from apps.core.operational_assessment import AssessmentUnavailable, assess
from apps.core.operational_snapshot import SnapshotUnavailable, collect_snapshot
from apps.core.operational_window import WindowUnavailable, load_window


class Command(BaseCommand):
    help = 'Combine durable counters and an optional observed window; never declares all-clear'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--input')
        parser.add_argument('--start', type=int)
        parser.add_argument('--end', type=int)

    def handle(self, *args, **options):
        supplied = [options['input'] is not None, options['start'] is not None, options['end'] is not None]
        if any(supplied) and not all(supplied):
            raise CommandError('Event input requires both integer window bounds')
        try:
            window = load_window(options['input'], options['start'], options['end']) if all(supplied) else None
            started = time.perf_counter()
            snapshot = collect_snapshot()
            result = assess(snapshot, window, collection_seconds=time.perf_counter() - started)
        except (WindowUnavailable, SnapshotUnavailable, AssessmentUnavailable) as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(result, sort_keys=True, allow_nan=False))
