from django.db import migrations


def prioritize(apps, schema_editor):
    RightsRequest = apps.get_model("safety", "RightsRequest")
    RightsRequest.objects.using(schema_editor.connection.alias).filter(
        kind="representation", priority=1
    ).update(priority=0)


class Migration(migrations.Migration):
    dependencies = [("safety", "0008_alter_rightsrequest_options_rightsrequest_priority")]
    operations = [migrations.RunPython(prioritize, migrations.RunPython.noop)]
