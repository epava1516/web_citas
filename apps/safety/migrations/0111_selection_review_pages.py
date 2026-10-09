from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("safety", "0110_recipient_execution_notices")]
    operations = [
        migrations.AddField(model_name="rightsportabilityselectionread", name="page_metadata",
                            field=models.JSONField(default=dict)),
        migrations.AddField(model_name="rightsportabilityselectionreview", name="page_reads",
                            field=models.JSONField(default=list)),
    ]
