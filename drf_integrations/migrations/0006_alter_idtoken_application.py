# Generated by Django 3.2.12 on 2022-05-03 11:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drf_integrations", "0005_idtoken"),
    ]

    operations = [
        migrations.AlterField(
            model_name="idtoken",
            name="application",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
            ),
        ),
    ]