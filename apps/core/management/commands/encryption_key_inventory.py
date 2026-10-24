"""Explicit private cipher inspection; no endpoint, scheduler or retirement action."""
import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.encryption_inventory import InventoryUnavailable, collect_inventory


class Command(BaseCommand):
    help = 'Inspect bounded encrypted DB cells; never authorize key retirement'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--inspect-ciphertext', action='store_true')
        parser.add_argument('--max-cells', type=int, default=1000)

    def handle(self, *args, **options):
        if not options['inspect_ciphertext']:
            raise CommandError('Explicit --inspect-ciphertext is required for private DB inspection')
        try:
            result = collect_inventory(options['max_cells'])
        except InventoryUnavailable as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(result, sort_keys=True, allow_nan=False))
