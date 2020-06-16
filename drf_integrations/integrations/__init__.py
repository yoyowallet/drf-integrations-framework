from drf_integrations.integrations.registry import Registry

default_registry = Registry()

register = default_registry.register
get = default_registry.get
get_all = default_registry.get_all
get_urls = default_registry.get_urls
