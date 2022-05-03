import copy
from django import forms

from drf_integrations import models
from drf_integrations.fields import get_json_field
from drf_integrations.integrations import Registry

JSONField = get_json_field()


class ApplicationInstallationForm(forms.ModelForm):
    """
    Application installation form that loads additional fields
    from an integration class.
    """

    class Meta:
        model = models.get_application_installation_model()
        fields = [
            "application",
            models.get_application_installation_install_attribute_name(),
            "api_client_name",
        ]

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

        self.integration_config_fields = []
        self.integration_form = None
        self.fields = copy.deepcopy(self.base_fields)
        use_config_class = False

        if self.instance.pk:
            try:
                use_config_class = self.instance.application.has_config_class
            except Registry.IntegrationUnavailableException:
                pass

        config = self.instance.get_config()

        # An empty string means default api_client_name. Since django treats null and
        # blank equally any null values are rendered as default api_client_name. To get
        # around this we add an option to be used as null.
        self.fields["api_client_name"].choices = [("-", "-")] + self.fields[
            "api_client_name"
        ].choices

        if self.initial.get("api_client_name") is None:
            self.initial["api_client_name"] = "-"

        if use_config_class:
            integration_class = self.instance.application.get_integration_instance()
            self.integration_form = integration_class.config_form_class
            for name, field in self.integration_form.base_fields.items():
                self.integration_config_fields.append(name)
                self.fields[name] = field
                self.initial[name] = config.get(name, field.initial)

        else:
            # Application has no integration
            # Render config field
            self.fields["config"] = JSONField(required=False)
            self.initial["config"] = config

    def clean(self):
        # Incoming empty string values are transformed to None by the clean method.
        # Thus we track if we have an incoming empty string for the default
        # api_client_name and restore the value after clean.
        is_default = self.data["api_client_name"] == ""
        data = super().clean()

        if data["api_client_name"] == "-":
            data["api_client_name"] = None
        elif is_default:
            data["api_client_name"] = ""

        if self.integration_form:
            data = self.integration_form.clean_form_data(self)

        return data

    def save(self, commit=True):
        if self.integration_form:
            self.instance.config = {
                name: self.cleaned_data.get(name) for name in self.integration_config_fields
            }
        else:
            self.instance.config = self.cleaned_data.get("config", {})

        return super().save(commit)
