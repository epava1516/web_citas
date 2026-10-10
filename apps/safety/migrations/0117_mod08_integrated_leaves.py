"""Join independently verified MOD08 migrations without rewriting their history."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0113_portability_export_jobs"),
        ("safety", "0114_rights_object_delivery"),
        ("safety", "0116_rights_evidence_runtime"),
    ]
    operations = []
