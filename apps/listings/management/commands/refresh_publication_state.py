from django.core.management.base import BaseCommand
from django.db import connection, transaction

from apps.listings.publication_state import mark_all, mark_stale, refresh_all, rules_version


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
            mark_all() if options["all"] else mark_stale()
            total = refresh_all()
        # A full recompute rewrites many rows; reclaim them so reads keep their plans.
        with connection.cursor() as cursor:
            for table in ("listings_publicationstate", "listings_publicationdirty"):
                cursor.execute(f"VACUUM ANALYZE {table}")
        self.stdout.write(f"Publication state current for rules {rules_version()[:12]}: {total} recomputed")
