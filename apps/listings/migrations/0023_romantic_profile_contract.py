"""Preserve legacy content; never relabel its approved revision as romantic."""

from django.db import migrations, models


def catalogue(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Service = apps.get_model("catalog", "Service")
    Category.objects.using(schema_editor.connection.alias).get_or_create(
        slug="romantic-dating",
        defaults={"name_es": "Citas románticas", "name_en": "Romantic dating", "version": 1},
    )
    legacy = Category.objects.using(schema_editor.connection.alias).filter(
        slug__in=["modeling", "social", "wellness"]
    )
    Service.objects.using(schema_editor.connection.alias).filter(category__in=legacy).update(
        active=False
    )
    legacy.update(active=False)
    # Persisted eligibility belongs to the prior rule, not to this new content policy.
    apps.get_model("listings", "PublicationState").objects.using(
        schema_editor.connection.alias
    ).update(eligible=False, rules_version="romantic-contract-migration")


class Migration(migrations.Migration):
    dependencies = [("listings", "0022_restore_conservative_publication_invalidation")]
    operations = [
        migrations.AddField(
            model_name="revision", name="content_contract",
            field=models.CharField(max_length=32, default="legacy-professional-v1", editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="revision", name="content_contract",
            field=models.CharField(max_length=32, default="romantic-v1", editable=False),
        ),
        # Rollback retains the new category and inactive legacy labels for audit.
        # It does not reactivate old publications or undo a content-policy decision.
        migrations.RunPython(catalogue, migrations.RunPython.noop),
    ]
