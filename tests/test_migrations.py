from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db
def test_no_missing_framework_migrations():
    stdout = StringIO()
    call_command(
        "makemigrations",
        "drf_integrations",
        check=True,
        dry_run=True,
        stdout=stdout,
    )


@pytest.mark.django_db(transaction=True)
def test_existing_client_secrets_are_safely_upgraded():
    executor = MigrationExecutor(connection)
    old_target = [("drf_integrations", "0006_alter_accesstoken_user_alter_application_user_and_more")]
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps
    Application = old_apps.get_model("drf_integrations", "Application")

    plaintext_secret = "legacy-plaintext-secret"
    recognised_hash = "md5$salt$7f8c27486f5a4e193e9a1b89bfbcdb5a"
    plaintext_app = Application.objects.create(
        client_id="plaintext-client",
        client_secret=plaintext_secret,
        client_type="confidential",
        authorization_grant_type="client-credentials",
    )
    hashed_app = Application.objects.create(
        client_id="hashed-client",
        client_secret=recognised_hash,
        client_type="confidential",
        authorization_grant_type="client-credentials",
    )

    executor = MigrationExecutor(connection)
    new_target = [("drf_integrations", "0008_hash_existing_application_client_secrets")]
    executor.migrate(new_target)
    new_apps = executor.loader.project_state(new_target).apps
    Application = new_apps.get_model("drf_integrations", "Application")

    plaintext_app = Application.objects.get(pk=plaintext_app.pk)
    hashed_app = Application.objects.get(pk=hashed_app.pk)

    from django.contrib.auth.hashers import check_password

    assert plaintext_app.client_secret != plaintext_secret
    assert check_password(plaintext_secret, plaintext_app.client_secret)
    assert hashed_app.client_secret == recognised_hash
