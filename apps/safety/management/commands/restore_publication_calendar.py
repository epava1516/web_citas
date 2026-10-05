"""Explicitly scoped calendar maintenance; preview rolls back all writes."""

import json

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.safety.publication_calendar_upgrade import restore_calendar


class Command(BaseCommand):
    help = "Validate and preview one publication calendar recovery; use --apply to persist."

    def add_arguments(self, parser):
        parser.add_argument("hold_id", type=int)
        parser.add_argument("--apply", action="store_true")

    @sensitive_variables()
    def handle(self, *args, **options):
        if options["hold_id"] < 1:
            raise CommandError("A positive measure identifier is required")
        try:
            with transaction.atomic():
                result = restore_calendar(options["hold_id"])
                if not options["apply"]:
                    transaction.set_rollback(True)
        except (ObjectDoesNotExist, ValidationError, DatabaseError):
            raise CommandError("Recovery unavailable; no changes applied") from None
        self.stdout.write(json.dumps({"applied": options["apply"], **result}, sort_keys=True))
