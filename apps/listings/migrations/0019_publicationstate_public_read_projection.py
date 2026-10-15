from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import migrations, models

MARK_EXISTING = "SELECT listings_publication_mark(ARRAY(SELECT id FROM listings_listing));"


class Migration(migrations.Migration):
    dependencies = [("listings", "0018_listing_public_page_order")]

    operations = [
        migrations.AddField("publicationstate", "expires_at", models.DateTimeField(null=True)),
        migrations.AddField("publicationstate", "published_at", models.DateTimeField(null=True)),
        migrations.AddField("publicationstate", "search_document", SearchVectorField(null=True)),
        migrations.AddIndex("publicationstate", models.Index(
            fields=["-published_at", "listing"], name="pub_state_page_order",
        )),
        migrations.AddIndex("publicationstate", GinIndex(
            fields=["search_document"], name="pub_state_search_doc_gin",
        )),
        migrations.RunSQL(MARK_EXISTING, MARK_EXISTING),
    ]
