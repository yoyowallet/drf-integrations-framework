from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IntegrationsExampleConfig(AppConfig):
    name = "example.drf_integrations_example"
    verbose_name = _("Integrations example")
