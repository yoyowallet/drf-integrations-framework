from typing import Dict, Iterable, List, Optional, Set, Type, Union

import inspect
from django.urls import include, path

from drf_integrations.exceptions import ImproperlyConfigured
from drf_integrations.integrations.base import BaseIntegration
from drf_integrations.utils import is_instance_of_all


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

    def get_all(
        self, *implements: Iterable[type], is_local: Optional[bool] = None
    ) -> Set[BaseIntegration]:
        """
        Get all integrations. If ``implements`` is provided, only return integrations
        that are instances of **all** of the classes in ``implements``.

        :raises TypeError: If any element of ``implements`` is not a type.
        """
        if is_local is not None:
            integrations = {
                value for value in self.integrations.values() if value.is_local is is_local
            }
        else:
            integrations = set(self.integrations.values())

        # Filter by implements
        return set(
            integration
            for integration in integrations
            if is_instance_of_all(integration, implements)
        )

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
                urls += [
                    path(
                        f"{basepath}{name}/",
                        include(
                            (integration_urls, integration_cls.namespace),
                            namespace=integration_cls.namespace,
                        ),
                    )
                ]
        return urls
