import pytest
from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import ViewSet

from drf_integrations.auth_backends import IntegrationOAuth2Authentication
from drf_integrations.integrations.base import Context
from tests.integration_samples import TestLocalWithFormIntegration
from tests.utils import WrapperResponse

REQUIRED_SCOPE = "my_scope"


class TestOAuthViewset(ViewSet):
    authentication_classes = (IntegrationOAuth2Authentication,)
    permission_classes = (TokenHasScope,)
    required_scopes = [REQUIRED_SCOPE]

    def create(self, request, *args, **kwargs):
        return WrapperResponse(request)


def test_oauth_backend_no_authentication():
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view({"post": "create"})
    request = factory.post("")

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_oauth_backend_no_authorization(get_integration, create_access_token):
    integration = get_integration(is_local=True, has_form=False)
    token_str = "token"
    create_access_token(
        target_id=1,
        application_kwargs=dict(local_integration_name=integration.name),
        token=token_str,
    )
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view({"post": "create"})
    request = factory.post("", HTTP_AUTHORIZATION=f"Bearer {token_str}")

    response = view(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_oauth_backend_internal_token(get_integration, create_access_token):
    integration = get_integration(is_local=True, has_form=False)
    token_str = "token"
    token, __ = create_access_token(
        target_id=1,
        application_kwargs=dict(local_integration_name=integration.name),
        token=token_str,
        scope=REQUIRED_SCOPE,
    )
    token.is_internal_only = True
    token.save()
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view({"post": "create"})
    request = factory.post("", HTTP_AUTHORIZATION=f"Bearer {token_str}")

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_oauth_backend_not_installed(get_integration, create_access_token):
    integration = get_integration(is_local=True, has_form=False)
    token_str = "token"
    __, installation = create_access_token(
        target_id=1,
        application_kwargs=dict(local_integration_name=integration.name),
        token=token_str,
        scope=REQUIRED_SCOPE,
    )
    installation.delete()
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view({"post": "create"})
    request = factory.post("", HTTP_AUTHORIZATION=f"Bearer {token_str}")

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_oauth_backend_pass(get_integration, create_access_token):
    integration = get_integration(is_local=True, has_form=False)
    token_str = "token"
    target_id = 1
    token, installation = create_access_token(
        target_id=target_id,
        application_kwargs=dict(local_integration_name=integration.name),
        token=token_str,
        scope=REQUIRED_SCOPE,
    )
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view({"post": "create"})
    request = factory.post("", HTTP_AUTHORIZATION=f"Bearer {token_str}")

    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.request.auth == token
    assert response.request.auth_context == Context(installation=installation)


class IntegrationSpecificAuthentication(IntegrationOAuth2Authentication):
    ensure_integration_classes = (TestLocalWithFormIntegration,)


@pytest.mark.django_db
def test_oauth_backend_cannot_ensure_integration(get_integration, create_access_token):
    integration = get_integration(is_local=True, has_form=False)
    token_str = "token"
    target_id = 1
    create_access_token(
        target_id=target_id,
        application_kwargs=dict(local_integration_name=integration.name),
        token=token_str,
        scope=REQUIRED_SCOPE,
    )
    factory = APIRequestFactory()
    view = TestOAuthViewset.as_view(
        {"post": "create"}, authentication_classes=(IntegrationSpecificAuthentication,)
    )
    request = factory.post("", HTTP_AUTHORIZATION=f"Bearer {token_str}")

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
