import itertools
from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

DEFAULT_SETTINGS = {
    "INSTALLED_INTEGRATIONS": [],
    "DB_BACKEND_JSON_FIELD": "",
    "INTEGRATIONS_APPLICATION_INSTALLATION_INSTALL_ATTRIBUTE": "target_id",
}

DEFAULT_MODEL_SETTINGS = {
    "OAUTH2_PROVIDER_APPLICATION_MODEL": "AbstractApplication",
    "OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL": "AbstractAccessToken",
    "OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL": "AbstractRefreshToken",
    "OAUTH2_PROVIDER_GRANT_MODEL": "AbstractGrant",
    "INTEGRATIONS_APPLICATION_INSTALLATION_MODEL": "AbstractApplicationInstallation",
}


class DRFIntegrationsConfig(AppConfig):
    name = "drf_integrations"
    verbose_name = _("Integrations")

    def ready(self):
        from drf_integrations import models
        from drf_integrations.integrations import register

        for name, default_value in itertools.chain(
            DEFAULT_SETTINGS.items(), DEFAULT_MODEL_SETTINGS.items()
        ):
            value = getattr(settings, name, None)
            if value is None:
                raise ImproperlyConfigured(f"{name} setting is required to run drf_integrations")
            elif name in DEFAULT_MODEL_SETTINGS:
                settings_model = apps.get_model(value)
                default_model = getattr(models, default_value)
                if not issubclass(settings_model, default_model):
                    raise ImproperlyConfigured(
                        f"Class for {name} must be a subclass of {default_value}"
                    )

        for installed_integration in settings.INSTALLED_INTEGRATIONS:
            integration_class = import_string(installed_integration)
            register(integration_class)
