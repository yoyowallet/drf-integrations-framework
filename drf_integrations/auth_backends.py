from typing import TYPE_CHECKING, Optional, Tuple

import logging
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import exceptions

from drf_integrations import models

if TYPE_CHECKING:
    from rest_framework.request import Request

    from drf_integrations.types import AnyUser


ApplicationInstallation = models.get_application_installation_model()


logger = logging.getLogger(__name__)


class IntegrationOAuth2Authentication(OAuth2Authentication):
    """
    Modified to:
    - Raise an AuthenticationFailed error when an invalid token is provided, and
    - Return an instance of AnonymousUser when the client credentials grant is used in
        the case of server-to-server communications.
    """

    ensure_integration_classes = ()

    def authenticate(self, request: "Request") -> "Optional[Tuple[AnyUser, models.AccessToken]]":
        result = super().authenticate(request)

        if hasattr(request, "oauth2_error") and request.oauth2_error:
            raise exceptions.AuthenticationFailed(
                detail=request.oauth2_error.get("error_description"),
                code=request.oauth2_error.get("error"),
            )

        if result:
            token = result[1]
            if token.is_internal_only:
                return None

            try:
                integration = token.application.get_integration_instance(
                    *self.ensure_integration_classes
                )
            except ValueError:
                return None

            try:
                installation = (
                    ApplicationInstallation.objects.select_related("application")
                    .active()
                    .get(
                        **integration.get_installation_lookup_from_request(
                            request=request, application=token.application
                        )
                    )
                )
            except (
                ApplicationInstallation.DoesNotExist,
                ApplicationInstallation.MultipleObjectsReturned,
            ):
                logger.exception("drf_integrations.auth_backends.invalid_installation")
                raise exceptions.AuthenticationFailed()

            request.auth_context = installation.get_context()

        return result
