import pytest
from django.urls import URLResolver, path
from django.urls.resolvers import RegexPattern

from drf_integrations.integrations import Registry
from drf_integrations.integrations.base import BaseIntegration
from tests.integration_samples import TestInternalIntegration, TestLocalIntegration


def test_register(get_integration):
    """
    Calling register correctly adds the integration
    """
    registry = Registry()
    assert len(registry.integrations) == 0
    integration = get_integration(register=False)
    registry.register(integration)
    assert len(registry.integrations) == 1
    assert integration.name in registry.integrations


def test_get(get_integration):
    """
    Calling get correctly fetches the integration (both by name and instance)
    """
    registry = Registry()
    integration = get_integration(is_local=False, register=False)
    registry.register(integration)
    assert registry.get(integration) == integration
    assert registry.get(integration.name) == integration

    with pytest.raises(Registry.IntegrationUnavailableException):
        registry.get(get_integration(is_local=True, register=False))

    with pytest.raises(ValueError):
        registry.get(2)


def test_get_all(get_integration):
    """
    Calling get_all correctly returns all, local or non-local integration sets
    """
    registry = Registry()
    integration1 = get_integration(is_local=True, register=False)
    registry.register(integration1)
    integration2 = get_integration(is_local=False, register=False)
    registry.register(integration2)
    assert registry.get_all() == {integration1(), integration2()}
    assert registry.get_all(is_local=True) == {integration1()}
    assert registry.get_all(is_local=False) == {integration2()}


def test_get_all_with_implements(get_integration):
    """
    Calling get_all with `implements` correctly returns all, local or non-local
    integration sets that inherit from all the classes in `implements`.
    """
    registry = Registry()
    integration1 = get_integration(is_local=True, register=False)
    registry.register(integration1)
    integration2 = get_integration(is_local=False, register=False)
    registry.register(integration2)
    assert registry.get_all(TestLocalIntegration) == {integration1()}
    assert registry.get_all(TestInternalIntegration) == {integration2()}
    assert registry.get_all(TestInternalIntegration, TestLocalIntegration) == set()
    with pytest.raises(TypeError):
        registry.get_all(integration2())


def test_get_urls():
    """
    Calling get_urls returns an URLConf with the correctly formed paths pointing to
    their corresponding views
    """
    registry = Registry()
    mock_request_handler = lambda request: None  # noqa: E731

    class TestIntegration(BaseIntegration):
        name = "some-integration"

        def get_urls(self):
            return [path("v1/path/", mock_request_handler)]

    registry.register(TestIntegration)
    urlconf = registry.get_urls()
    resolver = URLResolver(RegexPattern(r"^/"), urlconf)
    valid_paths = ["/api/integrations/some-integration/v1/path/"]
    for valid_path in valid_paths:
        resolver_match = resolver.resolve(valid_path)
        assert resolver_match.func == mock_request_handler
