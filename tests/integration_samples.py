from django import forms

from drf_integrations.integrations.base import BaseIntegration, BaseIntegrationForm


class FormTest(BaseIntegrationForm):
    extra_field = forms.CharField(max_length=10)

    @classmethod
    def clean_form_data(cls, installation_form: forms.Form) -> dict:
        data = super().clean_form_data(installation_form)
        if "extra_field" not in data or "forbidden" in data["extra_field"]:
            raise forms.ValidationError({"extra_field": "Value cannot be forbidden"})
        return data


class InternalIntegrationTest(BaseIntegration):
    name = "test_internal"
    is_local = False


class LocalIntegrationTest(BaseIntegration):
    name = "test_local"
    is_local = True


class InternalWithFormIntegrationTest(BaseIntegration):
    name = "test_internal_form"
    is_local = False
    config_form_class = FormTest


class LocalWithFormIntegrationTest(BaseIntegration):
    name = "test_local_form"
    is_local = True
    config_form_class = FormTest
