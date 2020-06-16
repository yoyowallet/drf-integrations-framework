import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import ViewSet

from drf_integrations import integrations
from drf_integrations.auth_backends import IntegrationOAuth2Authentication
from drf_integrations.integrations.base import Context
from drf_integrations.models import ApplicationInstallation
from tests.integration_samples import TestInternalWithFormIntegration
from tests.utils import WrapperResponse


class InternalPermission(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, AnonymousUser) and isinstance(
            request.successful_authenticator, InternalIntegrationAuthentication
        )


class IntegrationWithAuth(TestInternalWithFormIntegration):
    name = "test_internal_form_auth"

    @classmethod
    def get_installation_lookup_from_request(cls, request, application=None):
        return cls.get_installation_lookup_from_config_values(
            extra_field=request.headers.get("My-Header")
        )


class InternalIntegrationAuthentication(BaseAuthentication):
    def authenticate(self, request):
        integration = integrations.get(IntegrationWithAuth)
        try:
            installation = (
                ApplicationInstallation.objects.select_related("application")
                .active()
                .get(**integration.get_installation_lookup_from_request(request=request))
            )
        except (
            ApplicationInstallation.DoesNotExist,
            ApplicationInstallation.MultipleObjectsReturned,
        ):
            return None

        request.auth_context = installation.get_context()

        return AnonymousUser(), request.auth_context


class TestInternalViewset(ViewSet):
    authentication_classes = (
        IntegrationOAuth2Authentication,
        InternalIntegrationAuthentication,
    )
    permission_classes = (InternalPermission,)

    def create(self, request, *args, **kwargs):
        return WrapperResponse(request)


@pytest.mark.django_db
def test_multiple_auth_backends_none_valid(get_application):
    integration = integrations.register(IntegrationWithAuth)
    application = get_application(integration=integration)
    application.install(target_id=1, config=dict(extra_field="mysecret"))

    factory = APIRequestFactory()
    view = TestInternalViewset.as_view({"post": "create"},)
    request = factory.post("", HTTP_MY_HEADER="randomstr")

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_multiple_auth_backends_internal_pass(get_application):
    integration = integrations.register(IntegrationWithAuth)
    application = get_application(integration=integration)
    secret = "mysecret"
    installation = application.install(target_id=1, config=dict(extra_field=secret))
    context = Context(installation=installation)

    factory = APIRequestFactory()
    view = TestInternalViewset.as_view({"post": "create"},)
    request = factory.post("", HTTP_MY_HEADER=secret)

    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.request.successful_authenticator, InternalIntegrationAuthentication)
    assert isinstance(response.request.user, AnonymousUser)
    assert response.request.auth == context
    assert response.request.auth_context == context
