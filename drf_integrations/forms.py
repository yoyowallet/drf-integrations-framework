import copy

from django import forms

from drf_integrations import models
from drf_integrations.integrations import Registry


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

        if use_config_class:
            config = self.instance.get_config()
            integration_class = self.instance.application.get_integration_instance()
            self.integration_form = integration_class.config_form_class
            for name, field in self.integration_form.base_fields.items():
                self.integration_config_fields.append(name)
                self.fields[name] = field
                self.initial[name] = config.get(name, field.initial)

    def clean(self):
        data = super().clean()

        if self.integration_form:
            data = self.integration_form.clean_form_data(self)

        return data

    def save(self, commit=True):
        self.instance.config = {
            name: self.cleaned_data.get(name) for name in self.integration_config_fields
        }

        return super().save(commit)
