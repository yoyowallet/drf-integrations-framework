# Generated by Django 3.2.13 on 2022-05-03 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drf_integrations", "0003_auto_20210118_1317"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationinstallation",
            name="api_client_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="grant",
            name="redirect_uri",
            field=models.TextField(),
        ),
    ]
