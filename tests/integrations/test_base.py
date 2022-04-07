import copy
import pytest
from django import forms
from django.core.exceptions import ValidationError
from unittest.mock import Mock

from drf_integrations import integrations
from drf_integrations.integrations.base import Context
from tests import factories, integration_samples


class ParentForm(forms.Form):
    main_field = forms.IntegerField()

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.fields = copy.deepcopy(self.base_fields)
        for name, field in integration_samples.TestForm.base_fields.items():
            self.fields[name] = field


def test_clean_form_data_pass():
    """
    A ParentForm that expands on TestForm with correct values should be valid.
    """
    # The parent form inherits all fields from TestForm and their field validation
    form = ParentForm(data=dict(main_field="1", extra_field="value"))
    assert form.is_valid()
    # TestForm can validate the subset of fields corresponds to it
    data = integration_samples.TestForm.clean_form_data(form)
    assert data == {"main_field": 1, "extra_field": "value"}


def test_clean_form_data_fail():
    """
    A ParentForm that expands on TestForm with incorrect values should be valid,
    but when cleaning the TestForm it should fail.
    """
    # The parent form inherits all fields from TestForm and their field validation
    form = ParentForm(data=dict(main_field="1", extra_field="forbidden"))
    # It is valid because it only checks field validation
    assert form.is_valid()
    # When the same form is forwarded to TestForm validation it fails
    with pytest.raises(forms.ValidationError) as exc:
        integration_samples.TestForm.clean_form_data(form)

    assert exc.value.message_dict == {"extra_field": ["Value cannot be forbidden"]}


def test_clean(mocker):
    """
    .clean() should call clean_form_data so that specific validation is done
    """
    form = integration_samples.TestForm(data=dict(extra_field="value"))
    clean_form_data = mocker.patch.object(integration_samples.TestForm, "clean_form_data")
    assert form.is_valid()
    clean_form_data.assert_called_with(form)


@pytest.mark.parametrize("use_application", [True, False])
@pytest.mark.parametrize("use_installation", [True, False])
@pytest.mark.django_db
def test_set_initial_values(get_integration, get_application, use_application, use_installation):
    """
    .set_initial_values() should correctly store the passed arguments and
    it should fetch the correct values (if any) from them (i.e. installation)
    """
    # Nothing should be initialized in the integration
    integration = get_integration(has_form=True)
    form = integration.config_form_class(data=dict(extra_field="value"))
    assert not hasattr(form, "_target")
    assert not hasattr(form, "_application")
    assert not hasattr(form, "_installation")

    # Setup all combinations of parameters
    mock_target = Mock(pk=2)
    app = None
    installation = None
    initial_value = None
    if use_application:
        app = get_application(integration=integration)
        if use_installation:
            initial_value = "old value"
            installation = app.install(
                target_id=mock_target.pk, config=dict(extra_field=initial_value)
            )

    form.set_initial_values(target=mock_target, integration=integration(), application=app)

    # Check the form correctly stored and configured the parameters
    assert form._target == mock_target
    assert form._application == app
    assert form._installation == installation
    assert form.fields["extra_field"].initial == initial_value


@pytest.mark.django_db
def test_set_initial_values_wrong_integration(get_integration, get_application):
    """
    The applications integration and the given integration should match
    """
    integration1 = get_integration(is_local=True, has_form=True)
    integration2 = get_integration(is_local=False, has_form=True)
    form = integration1.config_form_class(data=dict(extra_field="value"))

    mock_target = Mock(pk=2)
    app = get_application(integration=integration1)

    with pytest.raises(ValueError):
        form.set_initial_values(target=mock_target, integration=integration2, application=app)


@pytest.mark.parametrize(
    ["has_form", "config"], [(True, dict(extra_field="value")), (False, None)]
)
def test_check_config(get_integration, has_form, config):
    """
    .check_config() is valid if the given Context installation is correct according to
    the integration's Form.
    """
    integration = get_integration(has_form=has_form)
    integration = integrations.get(integration)
    assert integration.check_config(
        Context(installation=factories.ApplicationInstallationFactory.build(config=config))
    )


@pytest.mark.parametrize(
    ["has_form", "config"], [(True, dict(extra_field="value")), (False, None)]
)
def test_check_config_fails(get_integration, has_form, config):
    """
    .check_config() raises an exception if the given Context installation is incorrect
    according to the integration's Form.
    """
    integration = get_integration(has_form=True)
    integration = integrations.get(integration)
    with pytest.raises(ValidationError) as exc:
        integration.check_config(
            Context(
                installation=factories.ApplicationInstallationFactory.build(
                    config=dict(main_field="1", extra_field="forbidden")
                )
            )
        )

    assert exc.value.message_dict == {"extra_field": ["Value cannot be forbidden"]}
