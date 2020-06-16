import inspect
from typing import Dict, List, Optional, Set, Type, Union

from django.urls import include, path

from drf_integrations.exceptions import ImproperlyConfigured
from drf_integrations.integrations.base import BaseIntegration


class Registry:
    class IntegrationUnavailableException(Exception):
        pass

    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}

    def register(self, integration_cls: Type[BaseIntegration], **kwargs) -> BaseIntegration:
        """Register an integration."""
        if integration_cls.name in self.integrations:
            raise ImproperlyConfigured(
                f"Integration with name {integration_cls.name} already registered"
            )
        self.integrations[integration_cls.name] = integration_cls(**kwargs)
        return self.integrations[integration_cls.name]

    def get_all(self, *, is_local: Optional[bool] = None) -> Set[BaseIntegration]:
        """Get all integrations."""
        if is_local is not None:
            return {value for value in self.integrations.values() if value.is_local is is_local}
        return set(self.integrations.values())

    def get(self, name_or_class: Union[str, Type[BaseIntegration]]) -> BaseIntegration:
        """
        Get integration by name or class.
        Raises Registry.IntegrationUnavailableException
        """
        try:
            if isinstance(name_or_class, str):
                integration = self.integrations[name_or_class]
            elif inspect.isclass(name_or_class) and issubclass(name_or_class, BaseIntegration):
                integration = self.integrations[name_or_class.name]
            else:
                raise ValueError("invalid name or base integration class")
        except KeyError:
            raise Registry.IntegrationUnavailableException()

        return integration

    def get_urls(self, basepath="api/integrations/") -> List:
        """Get URLConf for all registered integrations."""
        urls = []
        for name, integration_cls in self.integrations.items():
            # Legacy unprefixed URLs
            urls.extend(integration_cls.get_legacy_unprefixed_urls())

            # Integration URLs
            integration_urls = integration_cls.get_urls()
            if integration_urls:
                namespace = f"integration-{name}"
                urls += [
                    path(
                        f"{basepath}{name}/",
                        include((integration_urls, namespace), namespace=namespace),
                    )
                ]
        return urls
