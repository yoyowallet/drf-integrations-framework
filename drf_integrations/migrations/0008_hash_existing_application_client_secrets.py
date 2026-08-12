from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_existing_client_secrets(apps, schema_editor):
    Application = apps.get_model("drf_integrations", "Application")
    if Application._meta.swapped:
        return

    database_alias = schema_editor.connection.alias

    applications = Application._default_manager.using(database_alias).only(
        "pk", "client_secret", "hash_client_secret"
    )
    for application in applications.iterator():
        if not application.hash_client_secret:
            continue

        try:
            identify_hasher(application.client_secret)
        except ValueError:
            application.client_secret = make_password(application.client_secret)
            application.save(using=database_alias, update_fields=["client_secret"])


class Migration(migrations.Migration):
    dependencies = [
        ("drf_integrations", "0007_oauth_toolkit_2_4_schema"),
    ]

    operations = [
        migrations.RunPython(hash_existing_client_secrets, migrations.RunPython.noop),
    ]
