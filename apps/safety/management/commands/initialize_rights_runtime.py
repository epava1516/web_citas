"""Explicit migrator job for an isolated operator-managed Compose deployment."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from psycopg import sql

from apps.safety.evidence_chain import configure_role


class Command(BaseCommand):
    help = "Migrate and provision a separate runtime login from explicit environment secrets"

    def handle(self, *args, **options):
        role = os.environ.get("POSTGRES_RUNTIME_USER", "web_modelos_runtime")
        password = os.environ.get("POSTGRES_RUNTIME_PASSWORD")
        if not password:
            raise CommandError("POSTGRES_RUNTIME_PASSWORD is required")
        call_command("migrate", interactive=False)
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT current_user")
            if cursor.fetchone()[0] == role:
                raise CommandError("Migrator and runtime roles must differ")
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [role])
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"
                    ).format(sql.Identifier(role))
                )
            # Check pre-existing administrative/owner memberships before granting anything.
            configure_role(role)
            cursor.execute(
                sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(connection.settings_dict["NAME"]), sql.Identifier(role)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role))
            )
            cursor.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
                ).format(sql.Identifier(role))
            )
            cursor.execute(
                sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}").format(
                    sql.Identifier(role)
                )
            )
            configure_role(role)
        self.stdout.write("Separate runtime role provisioned; secret values omitted")
