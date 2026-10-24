"""Explicit bounded local report; no continuous receiver or external delivery."""
import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.operational_window import WindowUnavailable, load_window


class Command(BaseCommand):
    help = 'Aggregate a local JSONL event window; coverage and health remain unverified'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--input', required=True)
        parser.add_argument('--start', required=True, type=int)
        parser.add_argument('--end', required=True, type=int)

    def handle(self, *args, **options):
        try:
            report = load_window(options['input'], options['start'], options['end'])
        except WindowUnavailable as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False))
