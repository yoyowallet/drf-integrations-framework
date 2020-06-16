from typing import TypeVar

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from drf_integrations.integrations.base import BaseIntegration

IntegrationT = TypeVar("IntegrationT", bound=BaseIntegration)
AnyUser = TypeVar("AnyUser", settings.AUTH_USER_MODEL, AnonymousUser)
