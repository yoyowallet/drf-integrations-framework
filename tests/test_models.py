import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from drf_integrations import models
from tests import factories, integration_samples

pytestmark = pytest.mark.django_db


def test_get_application_installation_model():
    """
    .get_application_installation_model() points to the configured model in settings
    """
    assert (
        settings.INTEGRATIONS_APPLICATION_INSTALLATION_MODEL
        == "drf_integrations.ApplicationInstallation"
    )
    assert models.get_application_installation_model() == models.ApplicationInstallation


@pytest.mark.parametrize(
    ["internal_integration_name", "local_integration_name"],
    [
        ("integration1", None),  # Cannot have more than 1 internal integration with same name
        ("integration1", "integration2"),  # Cannot have both internal and local integration
    ],
)
def test_application_unique(internal_integration_name, local_integration_name):
    """
    Check the unique restrictions on internal integrations
    """
    factories.ApplicationFactory(internal_integration_name="integration1")
    with pytest.raises(IntegrityError):
        factories.ApplicationFactory(
            internal_integration_name=internal_integration_name,
            local_integration_name=local_integration_name,
        )


def test_sync_with_integration_registry(get_integration):
    """
    Check that synchronizing the integration registry correctly adds and deletes integrations
    """
    get_integration(is_local=True)
    get_integration(is_local=False)
    assert models.Application.objects.count() == 0
    # Add random outdated but approved internal integration application
    factories.ApplicationFactory(internal_integration_name="other", is_approved=True)
    assert models.Application.objects.count() == 1
    assert models.Application.objects.filter(is_approved=True).count() == 1
    # Sync registry
    models.Application.objects.sync_with_integration_registry()
    # There is a new Application
    assert models.Application.objects.count() == 2
    # There is still only 1 approved integration application
    app = models.Application.objects.filter(is_approved=True).get()
    # The application is internal and is not the outdated one, it is a new one
    assert app.is_internal_integration
    assert app.internal_integration_name != "other"


def test_get_integration_instance(get_integration):
    """
    .get_by_internal_integration() correctly creates (if needed) an Application for
    the given internal integration
    """
    internal_integration = get_integration(is_local=False)
    assert models.Application.objects.count() == 0
    app = models.Application.objects.get_by_internal_integration(
        integration_samples.TestInternalIntegration
    )
    assert models.Application.objects.count() == 1
    assert app.get_integration_instance() == integration_samples.TestInternalIntegration
    assert integration_samples.TestInternalIntegration == internal_integration

    app = models.Application.objects.get_by_internal_integration(
        integration_samples.TestInternalIntegration
    )
    assert models.Application.objects.count() == 1
    assert app.get_integration_instance() == integration_samples.TestInternalIntegration
    assert integration_samples.TestInternalIntegration == internal_integration


def test_get_integration_instance_local_error(get_integration):
    """
    .get_by_internal_integration() should fail for local integrations
    """
    local_integration = get_integration(is_local=True)
    assert models.Application.objects.count() == 0
    with pytest.raises(ValueError):
        models.Application.objects.get_by_internal_integration(type(local_integration))
    assert models.Application.objects.count() == 0


@pytest.mark.parametrize("is_local", [None, True, False])
@pytest.mark.parametrize("has_form", [True, False])
def test_has_config_class(get_integration, get_application, is_local, has_form):
    """
    An application has_config_class if it has both a configured integration and
    this integration has a related form
    """
    has_integration = is_local is not None
    if has_integration:
        integration = get_integration(is_local=is_local, has_form=has_form)
    else:
        integration = None
    app = get_application(integration=integration)
    assert app.has_config_class is (has_integration and has_form)


def test_install_uninstall_internal(get_integration, get_application):
    """
    Check an internal integration can be installed multiple times, and multiple calls
    on the same target simply overwrite the value and activate it
    """
    internal_application = get_application(integration=get_integration(is_local=False))
    assert models.ApplicationInstallation.objects.count() == 0

    internal_application.install(target_id=1)
    assert models.ApplicationInstallation.objects.count() == 1

    internal_application.install(target_id=2)
    assert models.ApplicationInstallation.objects.count() == 2
    installation = internal_application.install(target_id=2)
    assert models.ApplicationInstallation.objects.count() == 2

    installation.delete()
    assert models.ApplicationInstallation.objects.count() == 2
    assert models.ApplicationInstallation.objects.active().count() == 1

    internal_application.install(target_id=2)
    assert models.ApplicationInstallation.objects.count() == 2
    assert models.ApplicationInstallation.objects.active().count() == 2


def test_install_uninstall_local(get_integration, get_application):
    """
    Check a local integration can only be installed once, fails otherwise, but
    multiple calls on the same target simply overwrite the value and activate it
    """
    local_application = get_application(integration=get_integration(is_local=True))
    assert models.ApplicationInstallation.objects.count() == 0

    local_application.install(target_id=1)
    assert models.ApplicationInstallation.objects.count() == 1
    assert models.ApplicationInstallation.objects.active().count() == 1

    installation = local_application.install(target_id=1)
    assert models.ApplicationInstallation.objects.count() == 1

    installation.delete()
    assert models.ApplicationInstallation.objects.count() == 1
    assert models.ApplicationInstallation.objects.active().count() == 0

    local_application.install(target_id=2)
    assert models.ApplicationInstallation.objects.count() == 2
    assert models.ApplicationInstallation.objects.active().count() == 1

    with pytest.raises(ValidationError):
        local_application.install(target_id=1)


@pytest.mark.parametrize("is_local", [None, True, False])
@pytest.mark.parametrize(
    "invalid_form_values",
    [dict(), dict(extra_field="value too long"), dict(another_value="value")],
)
def test_install_check_config_fails(
    get_integration, get_application, is_local, invalid_form_values
):
    """
    On installation, an application without an integration configured, or if any,
    an incorrect config or a missing config if one is required, fails
    """
    if is_local is not None:
        integration = get_integration(is_local=is_local, has_form=True)
    else:
        integration = None
    app = get_application(integration=integration)
    with pytest.raises((ValueError, ValidationError)):
        app.install(target_id=1, config=invalid_form_values)


@pytest.mark.parametrize("is_local", [True, False])
def test_install_check_config_validates(get_integration, get_application, is_local):
    """
    An installation with a valid config succeeds
    """
    form_values = dict(extra_field="value")
    if is_local is not None:
        integration = get_integration(is_local=is_local, has_form=True)
    else:
        integration = None
    app = get_application(integration=integration)
    installation = app.install(target_id=1, config=form_values)
    assert models.ApplicationInstallation.objects.get() == installation
    assert installation.get_config() == form_values
    assert installation.deleted_at is None
