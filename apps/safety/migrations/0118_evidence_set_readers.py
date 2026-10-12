"""Read-side optimization only; stored evidence and producer functions unchanged."""
from django.db import migrations

from apps.safety.evidence_chain_bulk_sql_v1 import install, uninstall


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        install(cursor)


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        uninstall(cursor)


class Migration(migrations.Migration):
    dependencies = [("safety", "0117_mod08_integrated_leaves")]
    operations = [migrations.RunPython(forwards, backwards)]
