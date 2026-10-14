from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("listings", "0017_conditional_publication_dependencies")]

    operations = [
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(
                fields=["-published_at", "id"],
                condition=models.Q(status="published"),
                name="listing_public_page_order",
            ),
        ),
    ]
