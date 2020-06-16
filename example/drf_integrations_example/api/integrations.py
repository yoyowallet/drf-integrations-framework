from drf_integrations.integrations.base import BaseIntegration


class APIClientIntegration(BaseIntegration):
    name = "internal_api"
    is_local = True
