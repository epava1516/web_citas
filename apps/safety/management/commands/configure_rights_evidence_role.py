from django.core.management.base import BaseCommand
from django.db import transaction

from apps.safety.evidence_chain import configure_role


class Command(BaseCommand):
    help = "Configure an existing separate runtime role for immutable portability evidence"

    def add_arguments(self, parser):
        parser.add_argument("--role", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        configure_role(options["role"])
        self.stdout.write(
            "Configured evidence role; ordinary application grants remain operator-owned"
        )
