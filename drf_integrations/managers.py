from typing import TYPE_CHECKING, Type, Union

import datetime
import logging
from django.db import models
from django.utils import timezone
from oauth2_provider.models import ApplicationManager as BaseApplicationManager
from oauthlib.common import generate_token

if TYPE_CHECKING:
    from drf_integrations.integrations.base import BaseIntegration
    from drf_integrations.models import Application

logger = logging.getLogger(__name__)


class ApplicationManager(BaseApplicationManager):
    def _update_or_create_internal_integration(self, *, name: str) -> "Application":
        obj, __ = self.update_or_create(
            internal_integration_name=name,
            defaults=dict(
                name=f"{name} (Internal)",
                client_type=self.model.CLIENT_CONFIDENTIAL,
                is_approved=True,
            ),
        )
        return obj

    def get_by_internal_integration(
        self, name_or_class: "Union[str, Type[BaseIntegration]]"
    ) -> "Application":
        from drf_integrations import integrations

        integration_class = integrations.get(name_or_class)
        if integration_class.is_local:
            raise ValueError(
                f"An internal Application cannot be local, but {integration_class.display_name} is"
            )

        return self._update_or_create_internal_integration(name=integration_class.name)

    def sync_with_integration_registry(self):
        from drf_integrations import integrations

        installed_integrations = set(
            self.filter(is_approved=True).values_list("internal_integration_name", flat=True)
        )
        updated_integrations = set()

        for integration in integrations.get_all(is_local=False):
            self._update_or_create_internal_integration(name=integration.name)
            updated_integrations.add(integration.name)

        self.filter(
            internal_integration_name__in=installed_integrations - updated_integrations
        ).update(is_approved=False)


class ApplicationInstallationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)


class AccessTokenManager(models.Manager):
    def create_for_internal_integration(self, *, application: "Application"):
        """
        Creates an AccessToken that can be used only by internal applications,
        it won't be usable by external parties through an API. Useful when using
        an authentication backend different from OAuth2 but still want to link
        an authentication object to a request internally.
        """
        integration = application.get_integration_instance()
        if application.local_integration_name or integration.is_local:
            raise ValueError(
                "Cannot create an AccessToken for a local " f"integration: {integration.name}"
            )

        scope = " ".join(sorted(scope for scope in integration.default_scopes))
        now = timezone.now()
        token = generate_token()
        expires = now + datetime.timedelta(hours=12)

        return (
            self.filter(is_internal_only=True, expires__gt=now)
            .select_related("application")
            .get_or_create(
                application=application,
                scope=scope,
                defaults=dict(scope=scope, expires=expires, is_internal_only=True, token=token),
            )
        )
