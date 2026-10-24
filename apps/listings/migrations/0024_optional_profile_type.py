"""New profiles have no inferred type; keep every existing declared value."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("listings", "0023_romantic_profile_contract")]
    operations = [
        migrations.AlterField(
            model_name="revision",
            name="profile_type",
            field=models.CharField(max_length=20, blank=True, default=""),
        ),
    ]
