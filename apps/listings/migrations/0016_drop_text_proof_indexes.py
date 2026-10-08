from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("listings", "0015_publication_state")]

    operations = [
        migrations.RunSQL(
            "DROP INDEX IF EXISTS revision_text_unknown_v1; DROP INDEX IF EXISTS rate_text_unknown_v1;",
            migrations.RunSQL.noop,
        )
    ]
