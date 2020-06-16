from typing import TYPE_CHECKING, Dict, Optional, Tuple

import django
import pytest
from django.conf import settings
from django.utils.module_loading import import_string
from pytest_django.lazy_django import skip_if_no_django

from drf_integrations import integrations
from drf_integrations.integrations.base import BaseIntegration
from tests.integration_samples import (
    TestInternalIntegration,
    TestInternalWithFormIntegration,
    TestLocalIntegration,
    TestLocalWithFormIntegration,
)

if TYPE_CHECKING:
    from drf_integrations import models


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "drfintegrations",
                "USER": "postgres",
                "PASSWORD": None,
                "HOST": "localhost",
                "PORT": "5432",
            }
        },
        SITE_ID=1,
        SECRET_KEY="testing key",
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {"debug": True},
            },
        ],
        PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
        MIDDLEWARE=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.staticfiles",
            # drf_integrations specific setup
            "drf_integrations",
            "oauth2_provider",
        ),
        # drf_integrations specific setup
        DB_BACKEND_JSON_FIELD="django.contrib.postgres.fields.JSONField",
        INSTALLED_INTEGRATIONS=[],
        OAUTH2_PROVIDER_APPLICATION_MODEL="drf_integrations.Application",
        OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL="drf_integrations.AccessToken",
        OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL="drf_integrations.RefreshToken",
        OAUTH2_PROVIDER_GRANT_MODEL="drf_integrations.Grant",
        INTEGRATIONS_APPLICATION_INSTALLATION_MODEL="drf_integrations.ApplicationInstallation",
        INTEGRATIONS_APPLICATION_INSTALLATION_INSTALL_ATTRIBUTE="target",
    )

    django.setup()


@pytest.fixture(autouse=True)
def reset_registry():
    yield
    integrations.default_registry.integrations = dict()
    for installed_integration in settings.INSTALLED_INTEGRATIONS:
        integration_class = import_string(installed_integration)
        integrations.register(integration_class)


@pytest.fixture(scope="session")
def get_integration():
    def getter(*, is_local: bool = False, has_form: bool = False, register: bool = True):
        if is_local:
            if has_form:
                integration = TestLocalWithFormIntegration
            else:
                integration = TestLocalIntegration
        else:
            if has_form:
                integration = TestInternalWithFormIntegration
            else:
                integration = TestInternalIntegration

        if register:
            integrations.register(integration)

        return integration

    return getter


@pytest.fixture(scope="session")
def get_application():
    def getter(*, integration: Optional[BaseIntegration] = None):
        from tests import factories

        if integration:
            if integration.is_local:
                app = factories.ApplicationFactory(local_integration_name=integration.name)
            else:
                app = factories.ApplicationFactory(internal_integration_name=integration.name)
        else:
            app = factories.ApplicationFactory()
        return app

    return getter


@pytest.fixture
def drf_client():
    """
    Django Rest Framework APIClient instance. Adapted for DRF following
    `pytest_django.fixtures.rf` as a guide
    """
    skip_if_no_django()

    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(scope="session")
def create_access_token():
    from tests import factories

    def creator(
        *,
        target_id: int,
        installation_config: Optional[Dict] = None,
        application: "Optional[models.Application]" = None,
        application_kwargs: Optional[Dict] = None,
        token: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> "Tuple[models.AccessToken, models.ApplicationInstallation]":
        if not application:
            application = factories.ApplicationFactory(**(application_kwargs or dict()))
        installation = factories.ApplicationInstallationFactory(
            application_id=application.pk, target_id=target_id, config=installation_config,
        )
        token_obj = factories.AccessTokenFactory(
            application=application, token=token, scope=scope or ""
        )
        return token_obj, installation

    return creator
