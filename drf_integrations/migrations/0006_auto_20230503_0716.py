# Generated by Django 3.2.18 on 2023-05-03 07:16

import django.db.models.deletion
import oauth2_provider.generators
import oauth2_provider.models
from django.conf import settings
from django.db import migrations, models
from oauth2_provider.models import AbstractApplication

# ClientSecretField is not avaiable in early versions of the application.
is_client_secret_field = not isinstance(AbstractApplication.client_secret, models.CharField)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_ID_TOKEN_MODEL),
        ("drf_integrations", "0005_alter_applicationinstallation_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesstoken",
            name="id_token",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="access_token",
                to=settings.OAUTH2_PROVIDER_ID_TOKEN_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="application",
            name="algorithm",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "No OIDC support"),
                    ("RS256", "RSA with SHA-2 256"),
                    ("HS256", "HMAC with SHA-2 256"),
                ],
                default="",
                max_length=5,
            ),
        ),
        migrations.AddField(
            model_name="grant",
            name="claims",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="grant",
            name="nonce",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="application",
            name="authorization_grant_type",
            field=models.CharField(
                choices=[
                    ("authorization-code", "Authorization code"),
                    ("implicit", "Implicit"),
                    ("password", "Resource owner password-based"),
                    ("client-credentials", "Client credentials"),
                    ("openid-hybrid", "OpenID connect hybrid"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="application",
            name="client_secret",
            field=oauth2_provider.models.ClientSecretField(
                blank=True,
                db_index=True,
                default=oauth2_provider.generators.generate_client_secret,
                help_text="Hashed on Save. Copy it now if this is a new secret.",
                max_length=255,
            )
            if is_client_secret_field
            else models.CharField(
                blank=True,
                db_index=True,
                default=oauth2_provider.generators.generate_client_secret,
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="redirect_uri",
            field=models.TextField(),
        ),
    ]
