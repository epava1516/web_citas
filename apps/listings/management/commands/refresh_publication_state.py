from django.core.management.base import BaseCommand
from django.db import transaction

from apps.listings.publication_state import mark_all, refresh_all, rules_version


class Command(BaseCommand):
    help = (
        "Recompute stored publication state with the current code. Run after deploying "
        "rule changes before serving traffic, and with --all after restores that bypassed "
        "triggers (pg_restore --disable-triggers, session_replication_role=replica)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Mark every listing first")

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["all"]:
                mark_all()
            total = refresh_all()
        self.stdout.write(f"Publication state current for rules {rules_version()[:12]}: {total} recomputed")
