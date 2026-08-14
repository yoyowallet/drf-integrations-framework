import importlib
from io import StringIO

import pytest
from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

client_secret_migration = importlib.import_module(
    "drf_integrations.migrations.0008_hash_existing_application_client_secrets"
)


class TestMigrationState:
    """Guard the checked-in migration state against model drift."""

    @pytest.mark.django_db
    def test_no_missing_framework_migrations(self):
        """Fail when framework model changes lack a checked-in migration."""
        # Given the current framework models and checked-in migration graph
        stdout = StringIO()

        # When Django checks for model changes without corresponding migrations
        call_command(
            "makemigrations",
            "drf_integrations",
            check=True,
            dry_run=True,
            stdout=stdout,
        )

        # Then the command completes without reporting missing migration files


@pytest.mark.django_db(transaction=True)
class TestOAuth24MigrationUpgrade:
    """Exercise upgrades from the final DOT 1.4-compatible framework state.

    See https://django-oauth-toolkit.readthedocs.io/en/2.4.0/changelog.html.
    """

    old_target = [
        (
            "drf_integrations",
            "0006_alter_accesstoken_user_alter_application_user_and_more",
        )
    ]
    new_target = [("drf_integrations", "0008_hash_existing_application_client_secrets")]

    @pytest.fixture
    def migrate_application_model(self):
        """Provide exact migration transitions and their historical Application."""

        def migrate(target):
            """Migrate to ``target`` and render its historical Application model."""
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            return executor.loader.project_state(target).apps.get_model(
                "drf_integrations", "Application"
            )

        return migrate

    def test_existing_client_secrets_are_safely_upgraded(
        self,
        migrate_application_model,
        plaintext_client_secret,
        recognised_client_secret_hash,
    ):
        """Hash legacy plaintext while preserving recognized hashes exactly."""
        # Given a DOT 1.4-compatible database with plaintext and pre-hashed secrets
        old_application_model = migrate_application_model(self.old_target)
        plaintext_app = old_application_model.objects.create(
            client_id="plaintext-client",
            client_secret=plaintext_client_secret,
            client_type="confidential",
            authorization_grant_type="client-credentials",
        )
        hashed_app = old_application_model.objects.create(
            client_id="hashed-client",
            client_secret=recognised_client_secret_hash,
            client_type="confidential",
            authorization_grant_type="client-credentials",
        )

        # When the database is upgraded through the DOT 2.4 compatibility migrations
        upgraded_application_model = migrate_application_model(self.new_target)
        plaintext_app = upgraded_application_model.objects.get(pk=plaintext_app.pk)
        hashed_app = upgraded_application_model.objects.get(pk=hashed_app.pk)

        # Then plaintext is hashed and the existing recognized hash is unchanged
        assert plaintext_app.client_secret != plaintext_client_secret
        assert check_password(plaintext_client_secret, plaintext_app.client_secret)
        assert hashed_app.client_secret == recognised_client_secret_hash


class TestSwappedOAuth24Migration:
    """Ensure framework data migrations do not touch consumer-owned tables."""

    def test_client_secret_migration_skips_swapped_application(self, mocker):
        """Avoid querying a consumer-owned swapped Application table."""
        # Given a historical Application model swapped to a consumer project
        application_model = mocker.Mock()
        application_model._meta.swapped = "consumer.Application"
        historical_apps = mocker.Mock()
        historical_apps.get_model.return_value = application_model
        schema_editor = mocker.Mock()

        # When the framework client-secret migration runs
        client_secret_migration.hash_existing_client_secrets(
            historical_apps, schema_editor
        )

        # Then it exits without querying the consumer-owned table
        application_model._default_manager.using.assert_not_called()
