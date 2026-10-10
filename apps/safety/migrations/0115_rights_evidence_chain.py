import django.db.models.deletion
from django.db import migrations, models


def install(apps, schema_editor):
    from apps.safety.evidence_chain_sql_v1 import install

    with schema_editor.connection.cursor() as cursor:
        install(cursor)


def uninstall(apps, schema_editor):
    from apps.safety.evidence_chain_sql_v1 import uninstall

    with schema_editor.connection.cursor() as cursor:
        uninstall(cursor)


class Migration(migrations.Migration):
    dependencies = [("safety", "0111_selection_review_pages")]
    operations = [
        migrations.CreateModel(
            name="RightsEvidenceHead",
            fields=[
                (
                    "request",
                    models.OneToOneField(
                        to="safety.rightsrequest",
                        primary_key=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.PROTECT,
                    ),
                ),
                ("sequence", models.PositiveBigIntegerField(default=0)),
                ("digest", models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name="RightsEvidenceEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sequence", models.PositiveBigIntegerField()),
                ("kind", models.CharField(max_length=12)),
                ("source_table", models.CharField(max_length=100)),
                ("source_pk", models.CharField(max_length=64)),
                ("payload_digest", models.CharField(max_length=64)),
                ("previous_digest", models.CharField(max_length=64)),
                ("digest", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField()),
                (
                    "request",
                    models.ForeignKey(
                        to="safety.rightsrequest", on_delete=django.db.models.deletion.PROTECT
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("request", "sequence"), name="rights_chain_sequence_once"
                    ),
                    models.UniqueConstraint(
                        fields=("source_table", "source_pk"),
                        condition=models.Q(kind="row"),
                        name="rights_chain_source_once",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(sequence__gte=1), name="rights_chain_positive"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(kind__in=["row", "tombstone"]), name="rights_chain_kind"
                    ),
                ]
            },
        ),
        migrations.RunPython(install, uninstall),
    ]
