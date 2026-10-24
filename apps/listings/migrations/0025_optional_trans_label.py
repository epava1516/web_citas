"""An explicit display option, never inferred from a type or historical data."""

from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError


def preserve_selected_labels(apps, schema_editor):
    revision = apps.get_model("listings", "Revision")
    if revision.objects.using(schema_editor.connection.alias).filter(show_trans_label=True).exists():
        raise IrreversibleError(
            "Selected profile labels must be preserved; use compatible code or a reviewed restore"
        )


class Migration(migrations.Migration):
    dependencies = [("listings", "0024_optional_profile_type")]
    operations = [
        migrations.AddField(
            model_name="revision", name="show_trans_label",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrations.RunPython.noop, preserve_selected_labels),
    ]
