from drf_integrations.auth_backends import IntegrationOAuth2Authentication

from .integrations import APIClientIntegration


class OAuth2Authentication(IntegrationOAuth2Authentication):
    ensure_integration_classes = (APIClientIntegration,)
