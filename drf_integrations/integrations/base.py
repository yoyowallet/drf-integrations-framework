from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

import copy
from django import forms
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from rest_framework.request import Request

    from drf_integrations import models


@dataclass
class Context:
    installation: "models.AbstractApplicationInstallation"


class BaseIntegrationForm(forms.Form):
    @classmethod
    def _get_install_attribute_id_name(cls):
        from drf_integrations import models

        return models.get_application_installation_install_attribute_name()

    @classmethod
    def _get_install_attribute_name(cls):
        return f"_{cls._get_install_attribute_id_name()[:-3]}"

    @classmethod
    def clean_form_data(cls, installation_form: forms.Form) -> Dict:
        """
        Performs form-wide cleaning. `installation_form` will be a form that contains,
        at least, all the fields that the current class does, as long as it has not been
        tampered with or is missing values due to changes in the config schema. In order
        to better support the internal admin form functionality, usually it will also
        contain (but not always!) a field with the defined ApplicationInstallation
        install attribute ID (i.e. target_id).

        An example of this is when drf_integrations.forms.ApplicationInstallationForm
        is submitted in admin. At that stage, its clean method will be called, but not
        the clean method in this form. Instead, this hook is called, so that this
        integration form can also clean the data based on the integration criteria.
        """
        return installation_form.cleaned_data

    def clean(self) -> Dict:
        """
        Hook for doing any extra form-wide cleaning after Field.clean() has been
        called on every field.

        This implementation will directly call its own `clean_form_data`. This way,
        all the clean functionality can be uniquely defined under `clean_form_data` and
        always be called no matter where the clean process takes place.
        """
        data = super().clean()

        target_id_name = self._get_install_attribute_id_name()
        target_name = self._get_install_attribute_name()

        target = getattr(self, target_name, None)
        if target_id_name not in data and target:
            data[target_id_name] = target.pk

        try:
            data = self.clean_form_data(self)
        except ValidationError as exc:
            self.add_error(None, exc)

        return data

    def set_initial_values(
        self,
        *,
        target,
        integration: "BaseIntegration",
        application: "Optional[models.Application]" = None,
        **kwargs,
    ):
        """
        Sets initial values for the given kwargs and sets them as disabled.
        Useful for automated display of forms.
        """
        target_id_name = self._get_install_attribute_id_name()
        target_name = self._get_install_attribute_name()
        setattr(self, target_name, target)

        self._application = application
        self._installation = None
        if self._application:
            integration_check = self._application.get_integration_instance(integration.__class__)
            if integration != integration_check:
                raise ValueError(
                    f"Provided integration {integration} does not match for "
                    f"given application {self._application}"
                )
            target_filter = {target_id_name: target.pk}
            self._installation = self._application.installations.filter(**target_filter).first()

        if self._installation:
            config = self._installation.get_config()

            for name, field in self.base_fields.items():
                self.fields[name].initial = config.get(name, field.initial)


class BaseClient(object):
    def __init__(self, **kwargs):
        ...

    @classmethod
    def from_context(cls, context: Context, **kwargs) -> "BaseClient":
        initkwargs = copy.deepcopy(context.installation.get_config())
        initkwargs.update(kwargs)
        return cls(**initkwargs)


class BaseIntegration:
    name: str
    url: Optional[str]
    config_form_class: Optional[Type[BaseIntegrationForm]] = None
    client_class: Optional[Type[BaseClient]] = None
    is_local: bool = False
    is_installable: bool = True
    is_uninstallable: bool = False

    def __init__(self, **kwargs):
        ...

    def __eq__(self, other):
        """
        Unless the integration has a parameterizable init, two instances will be
        equal as long as their name is the same
        """
        return self.name == other.name

    def __hash__(self):
        """
        Unless the integration has a parameterizable init, two instances will be
        equal as long as their name is the same, so their hash can be evaluated purely
        from their name
        """
        return hash(self.name)

    @property
    def display_name(self) -> str:
        """
        Name to be displayed for installation if the integration is not local.
        """
        return self.name

    @property
    def namespace(self) -> str:
        """
        The URL namespace in which URLs for this integration should be included.
        """
        return f"integration-{self.name}"

    @property
    def default_scopes(self) -> List[str]:
        """
        List of default scopes for the integration, if any.
        """
        return []

    def get_urls(self) -> List:
        """
        Return URLs for this integration in the same way as a URLconf.
        The URLs will be nested under the path: `/api/integrations/<name>/`
        """
        return []

    def get_legacy_unprefixed_urls(self):
        """
        Return URLs for this integration in the same way as a URLconf.
        The URLs will be nested under the root path: `/`.

        This method is for legacy endpoints which do not follow the URL naming
        conventions, easing the transition to the integrations framework.
        """
        return []

    def get_config(self, context: Context) -> Optional[Dict[str, Any]]:
        """
        Get configuration values from the installation in the context.

        Override if you want to customise the return value (e.g. custom class).
        """
        return context.installation.config

    def check_config(self, context: Context) -> bool:
        """
        Check the validity of the configuration values.

        :raises forms.ValidationError: If config is not valid
        """
        if self.config_form_class:
            config = self.get_config(context)
            form = self.config_form_class(config)
            if not form.is_valid():
                raise forms.ValidationError(form.errors.as_data())
        return True

    def get_client(self, context: Context, **kwargs) -> BaseClient:
        """Return the API client for the integration."""
        return self.client_class.from_context(context, **kwargs)

    @classmethod
    def get_installation_lookup_from_config_values(cls, **kwargs) -> Dict:
        """
        Return a lookup filter suitable for models that subclass
        `drf_integrations.models.AbstractApplicationInstallation`.
        The filter should always return just 1 result.

        :param kwargs: Config values to uniquely identify an installation
        """
        kwargs = {f"config__{key}": value for key, value in kwargs.items()}
        if cls.is_local:
            kwargs.update(application__local_integration_name=cls.name)
        else:
            kwargs.update(application__internal_integration_name=cls.name)
        return kwargs

    @classmethod
    def get_installation_lookup_from_request(
        cls, request: "Request", *, application: "Optional[models.Application]" = None, **kwargs
    ) -> Dict:
        """
        Return a lookup filter suitable for models that subclass
        `drf_integrations.models.AbstractApplicationInstallation`.
        The filter should always return just 1 result.

        :param request: DRF request object
        :param application: Application linked to the authorised request
        """
        if cls.is_local:
            if not application:
                raise ValueError(
                    "A local integration is installed only once per Application, "
                    "the application argument is necessary to be able to look it up"
                )
            # Local integrations only have 1 installation always, so simply retrieve it
            return dict(application__local_integration_name=cls.name, application=application)

        # Internal integrations may have different behaviours (links an installation
        # config field to a request header, a cookie...), so each subclass should
        # define its own behaviour
        raise NotImplementedError()
