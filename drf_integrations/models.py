from typing import TYPE_CHECKING, Dict, List, Optional, Type

import urllib.parse
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, router, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _L
from oauth2_provider.models import AbstractAccessToken as OAuthAbstractAccessToken
from oauth2_provider.models import AbstractApplication as OAuthAbstractApplication
from oauth2_provider.models import AbstractGrant as OAuthAbstractGrant
from oauth2_provider.models import AbstractRefreshToken as OAuthAbstractRefreshToken
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.settings import oauth2_settings
from uuid import uuid4

from drf_integrations import managers
from drf_integrations.fields import get_json_field
from drf_integrations.types import IntegrationT

JSONField = get_json_field()

if TYPE_CHECKING:
    from rest_framework.request import Request

    from drf_integrations.integrations.base import Context


def get_application_installation_model() -> "AbstractApplicationInstallation":
    """Return the AccessToken model that is active in this project."""
    return apps.get_model(settings.INTEGRATIONS_APPLICATION_INSTALLATION_MODEL)


def get_application_installation_install_attribute_name():
    attr = settings.INTEGRATIONS_APPLICATION_INSTALLATION_INSTALL_ATTRIBUTE
    if not attr.endswith("_id"):
        attr = f"{attr}_id"
    return attr


class AbstractApplication(OAuthAbstractApplication):
    name = models.CharField(max_length=255)
    logo = models.ImageField(blank=True)
    description = models.TextField()
    website_url = models.URLField()
    is_approved = models.BooleanField(default=False)
    allowed_scopes = models.TextField(null=True, blank=True)
    internal_integration_name = models.TextField(
        null=True,
        blank=True,
        default=None,
        help_text="Internal integration name.",
        editable=False,
        unique=True,
    )
    local_integration_name = models.TextField(
        null=True,
        blank=True,
        default=None,
        help_text="Local integration name, specific to just one client.",
        editable=False,
    )

    objects = managers.ApplicationManager()

    class Meta(OAuthAbstractApplication.Meta):
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=~models.Q(
                    internal_integration_name__isnull=False,
                    local_integration_name__isnull=False,
                ),
                name="check_one_integration_set",
            )
        ]

    #
    # Overrides: oauth2_provider
    #

    def allows_grant_type(self, *grant_types) -> bool:
        """
        Overridden to support client credentials grant always and
        grant selected by the application.

        The client credentials grant is suitable for machine-to-machine authentication
        where a specific user's permission to access data is not required.
        """
        allowed_grant_types = {
            self.authorization_grant_type,
            self.GRANT_CLIENT_CREDENTIALS,
        }
        return bool(allowed_grant_types & set(grant_types))

    def is_usable(self, request: "Request") -> bool:
        """
        Determines whether the application can be used.
        """
        return self.is_approved

    def get_allowed_schemes(self) -> List[str]:
        """
        Overridden to take schemes from the value of `redirect_uris`.
        """
        schemes = set()
        for allowed_uri in self.redirect_uris.split():
            parsed_allowed_uri = urllib.parse.urlparse(allowed_uri)
            if parsed_allowed_uri.scheme:
                schemes.add(parsed_allowed_uri.scheme)
        return list(schemes)

    def valid_scopes_access(self) -> Dict[str, str]:
        """
        Returns a dictionary of allowed scope names (as keys)
        with their descriptions (as values).
        """
        all_scopes = get_scopes_backend().get_all_scopes()
        token_scopes = self.allowed_scopes.split() if self.allowed_scopes else []
        return {name: desc for name, desc in all_scopes.items() if name in token_scopes}

    @property
    def status_text(self) -> str:
        if self.is_approved:
            return _L("Live")
        else:
            return _L("Pending approval")

    def get_authorization_url(self, response_type="code", state=None) -> Optional[str]:
        if not self.redirect_uris:
            return None
        if state is None:
            state = str(uuid4())
        return "{}?{}".format(
            reverse("login_oauth2_provider:authorize"),
            urllib.parse.urlencode(
                {
                    "client_id": self.client_id,
                    "response_type": response_type,
                    "state": state,
                    "redirect_uri": self.default_redirect_uri,
                }
            ),
        )

    #
    # Properties: Integration
    #

    @property
    def is_internal_integration(self) -> bool:
        """
        Determines whether this application is an internal integration.
        """
        return self.internal_integration_name is not None

    def get_integration_instance(self, *ensure_subclasses: Type[IntegrationT]) -> IntegrationT:
        """
        Returns the instance of the integration class of this application.

        Ensures that the instance of the integration class is a subclass of
        `subclasses`. This is also useful for type hinting.
        """
        from drf_integrations import integrations

        if not self.internal_integration_name and not self.local_integration_name:
            raise ValueError("application is not linked to an integration")

        integration = integrations.get(
            self.internal_integration_name or self.local_integration_name
        )

        for subclass in ensure_subclasses:
            if not isinstance(integration, subclass):
                raise ValueError(f"integration {integration} is not a subclass of {subclass}")

        return integration

    @property
    def has_config_class(self) -> bool:
        return (
            bool(self.internal_integration_name or self.local_integration_name)
            and self.get_integration_instance().config_form_class is not None
        )

    #
    # Mutators: Installation
    #

    def install(self, target_id: int, *, config: Dict = None) -> "AbstractApplicationInstallation":
        integration = self.get_integration_instance()
        application_installation = get_application_installation_model()
        target_filter = {get_application_installation_install_attribute_name(): target_id}
        if self.local_integration_name:
            other_installations = application_installation.objects.filter(
                application=self, deleted_at__isnull=True
            ).exclude(**target_filter)
            if other_installations.exists():
                raise ValidationError(
                    "Cannot install this local application to more than one target"
                )

        with transaction.atomic(using=router.db_for_write(application_installation)):
            installation, __ = application_installation.objects.update_or_create(
                application=self,
                **target_filter,
                defaults={"config": config, "deleted_at": None},
            )
            if self.has_config_class:
                integration.check_config(installation.get_context())

        return installation

    def uninstall(self, target_id: int) -> "AbstractApplicationInstallation":
        application_installation = get_application_installation_model()
        target_filter = {get_application_installation_install_attribute_name(): target_id}
        installation = application_installation.objects.get(application=self, **target_filter)
        installation.delete()
        return installation


class Application(AbstractApplication):
    class Meta(AbstractApplication.Meta):
        swappable = "OAUTH2_PROVIDER_APPLICATION_MODEL"


class AbstractAccessToken(OAuthAbstractAccessToken):
    is_internal_only = models.BooleanField(default=False, editable=False)

    objects = managers.AccessTokenManager()

    class Meta(OAuthAbstractAccessToken.Meta):
        abstract = True


class AccessToken(AbstractAccessToken):
    class Meta(AbstractAccessToken.Meta):
        swappable = "OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL"


class AbstractRefreshToken(OAuthAbstractRefreshToken):
    class Meta(OAuthAbstractRefreshToken.Meta):
        abstract = True


class RefreshToken(AbstractRefreshToken):
    class Meta(AbstractRefreshToken.Meta):
        swappable = "OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL"


class AbstractGrant(OAuthAbstractGrant):
    class Meta(OAuthAbstractGrant.Meta):
        abstract = True


class Grant(AbstractGrant):
    class Meta(AbstractGrant.Meta):
        swappable = "OAUTH2_PROVIDER_GRANT_MODEL"


def _get_application_installation_class():
    class _AbstractApplicationInstallation(models.Model):
        class Meta:
            abstract = True
            unique_together = [
                ("application", get_application_installation_install_attribute_name())
            ]

        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        deleted_at = models.DateTimeField(null=True, editable=False)

        application = models.ForeignKey(
            oauth2_settings.APPLICATION_MODEL,
            on_delete=models.PROTECT,
            related_name="installations",
        )
        config = JSONField(null=True, blank=True)
        api_client_name = models.CharField(max_length=255, null=True, blank=True)

        objects = managers.ApplicationInstallationQuerySet.as_manager()

        def __str__(self):
            try:
                return (
                    f"{self.application.get_integration_instance().name} installation for "
                    f"{getattr(self, get_application_installation_install_attribute_name())}"
                )
            except ValueError:
                return (
                    f"Installation for "
                    f"{getattr(self, get_application_installation_install_attribute_name())}"
                )

        def get_config(self) -> Dict:
            return self.config or {}

        def get_context(self) -> "Context":
            from drf_integrations.integrations.base import Context

            return Context(installation=self)

        def get_external_data_source_lookup(self) -> Dict:
            """
            Return a lookup filter suitable for models that subclass
            `drf_integrations.integrations.models.BasePerformedByIntegration`.
            """
            return {"performed_by_installation_id": self.pk}

        def delete(self, using=None, keep_parents=False):
            using = using or router.db_for_write(self.__class__, instance=self)
            self.deleted_at = timezone.now()
            self.save(using=using)

    _AbstractApplicationInstallation.add_to_class(
        get_application_installation_install_attribute_name(),
        models.PositiveIntegerField(),
    )

    return _AbstractApplicationInstallation


AbstractApplicationInstallation = _get_application_installation_class()


class ApplicationInstallation(AbstractApplicationInstallation):
    class Meta(AbstractApplicationInstallation.Meta):
        swappable = "INTEGRATIONS_APPLICATION_INSTALLATION_MODEL"
