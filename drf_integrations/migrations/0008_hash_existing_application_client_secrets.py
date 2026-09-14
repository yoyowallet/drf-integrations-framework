from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_existing_client_secrets(apps, schema_editor):
    """Hash legacy plaintext OAuth client secrets during the DOT 2.4 upgrade.

    Django OAuth Toolkit 2.x stores client secrets using Django password hashers.
    This migration converts existing plaintext values while preserving secrets
    already recognized as Django hashes, preventing accidental double hashing.

    Applications that explicitly disable hashing are skipped. If Application is
    swapped, the migration does nothing because the consuming project owns the
    concrete table and must migrate it separately.

    The original plaintext credential remains the value clients must present for
    authentication; the stored hash is never a usable client secret.

    See:
    https://django-oauth-toolkit.readthedocs.io/en/2.4.0/changelog.html
    """
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
            # A recognized encoded value has already been hashed and must be
            # preserved byte-for-byte to avoid invalidating the client secret.
            identify_hasher(application.client_secret)
        except ValueError:
            application.client_secret = make_password(application.client_secret)
            application.save(using=database_alias, update_fields=["client_secret"])


class Migration(migrations.Migration):
    dependencies = [
        ("drf_integrations", "0007_oauth_toolkit_2_4_schema"),
    ]

    operations = [
        # Hashing is intentionally irreversible. Rolling this migration back
        # cannot recover plaintext secrets; recovery requires a pre-upgrade
        # database backup or rotation of the affected client credentials.
        migrations.RunPython(
            hash_existing_client_secrets,
            migrations.RunPython.noop,
        ),
    ]
