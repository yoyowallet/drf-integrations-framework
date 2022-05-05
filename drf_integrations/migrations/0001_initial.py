# Generated by Django 3.0.7 on 2020-06-13 18:38

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
import oauth2_provider.generators
from django.conf import settings
from django.db import migrations, models

from drf_integrations.fields import get_json_field
from drf_integrations.models import get_application_installation_install_attribute_name

JSONField = get_json_field()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("oauth2_provider", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessToken",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("token", models.CharField(max_length=255, unique=True)),
                ("expires", models.DateTimeField()),
                ("scope", models.TextField(blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("is_internal_only", models.BooleanField(default=False, editable=False)),
            ],
            options={"abstract": False, "swappable": "OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL"},
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "client_id",
                    models.CharField(
                        db_index=True,
                        default=oauth2_provider.generators.generate_client_id,
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "redirect_uris",
                    models.TextField(blank=True, help_text="Allowed URIs list, space separated"),
                ),
                (
                    "client_type",
                    models.CharField(
                        choices=[("confidential", "Confidential"), ("public", "Public")],
                        max_length=32,
                    ),
                ),
                (
                    "authorization_grant_type",
                    models.CharField(
                        choices=[
                            ("authorization-code", "Authorization code"),
                            ("implicit", "Implicit"),
                            ("password", "Resource owner password-based"),
                            ("client-credentials", "Client credentials"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "client_secret",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default=oauth2_provider.generators.generate_client_secret,
                        max_length=255,
                    ),
                ),
                ("skip_authorization", models.BooleanField(default=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("logo", models.ImageField(blank=True, upload_to="")),
                ("description", models.TextField()),
                ("website_url", models.URLField()),
                ("is_approved", models.BooleanField(default=False)),
                ("allowed_scopes", models.TextField(blank=True, null=True)),
                (
                    "internal_integration_name",
                    models.TextField(
                        blank=True,
                        default=None,
                        editable=False,
                        help_text="Internal integration name.",
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "local_integration_name",
                    models.TextField(
                        blank=True,
                        default=None,
                        editable=False,
                        help_text="Local integration name, specific to just one client.",
                        null=True,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drf_integrations_application",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "swappable": "OAUTH2_PROVIDER_APPLICATION_MODEL"},
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("token", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("revoked", models.DateTimeField(null=True)),
                (
                    "access_token",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="refresh_token",
                        to=settings.OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL,
                    ),
                ),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drf_integrations_refreshtoken",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
                "unique_together": {("token", "revoked")},
                "swappable": "OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL",
            },
        ),
        migrations.CreateModel(
            name="Grant",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=255, unique=True)),
                ("expires", models.DateTimeField()),
                ("redirect_uri", models.CharField(max_length=255)),
                ("scope", models.TextField(blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drf_integrations_grant",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "swappable": "OAUTH2_PROVIDER_GRANT_MODEL"},
        ),
        migrations.AddField(
            model_name="accesstoken",
            name="application",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="accesstoken",
            name="source_refresh_token",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="refreshed_access_token",
                to=settings.OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="accesstoken",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="drf_integrations_accesstoken",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="ApplicationInstallation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(editable=False, null=True)),
                ("config", JSONField(null=True)),
                (
                    get_application_installation_install_attribute_name(),
                    models.PositiveIntegerField(),
                ),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="installations",
                        to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
                "swappable": "INTEGRATIONS_APPLICATION_INSTALLATION_MODEL",
                "unique_together": {
                    ("application", get_application_installation_install_attribute_name())
                },
            },
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("internal_integration_name__isnull", False),
                    ("local_integration_name__isnull", False),
                    _negated=True,
                ),
                name="check_one_integration_set",
            ),
        ),
    ]
