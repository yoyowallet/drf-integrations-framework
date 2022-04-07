# Generated by Django 3.2.12 on 2022-04-07 08:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_ID_TOKEN_MODEL),
        ("drf_integrations", "0003_auto_20210118_1317"),
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
            model_name="applicationinstallation",
            name="api_client_name",
            field=models.CharField(blank=True, max_length=255, null=True),
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
            model_name="grant",
            name="redirect_uri",
            field=models.TextField(),
        ),
    ]
