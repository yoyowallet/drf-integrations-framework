# DRF Integrations Framework

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fyoyowallet%2Fdrf-integrations-framework%2Fbadge%3Fref%3Dmaster&style=flat)](https://actions-badge.atrox.dev/yoyowallet/drf-integrations-framework/goto?ref=master)

DRF Integrations Framework is a toolkit that plugs in to [Django REST Framework](https://www.django-rest-framework.org/)
and simplifies the management of third party integrations. If you find yourself connecting to multiple services with
different sets of credentials, or handling multiple inbound requests from third party services, DRF Integrations
Framework will probably simplify that for you. DRF Integrations Framework will help you split the responsibilities
between the source/destiny of events, how these requests are authenticated and the business logic associated to them.

## Requirements
- Python 3.7+
- Django 2.2+
- Django REST Framework 3.9.2+
- Django OAuth Toolkit 1.3+
- Pillow 7+

## Installation

The following library is required in order to build on `Linux systems`. It fixes the
problem where `Error: pg_config executable not found.` is given when installing psycopg2
via `poetry install`
```
sudo apt install libpq-dev
```

Install from PyPi:
```bash
pip install drf-integrations-framework
```
Or install from source:
```bash
pip install https://github.com/yoyowallet/drf-integrations-framework/archive/v0.7.1.tar.gz
```

Add the apps to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...,
    "rest_framework",
    "oauth2_provider",
    "drf_integrations",
]
```

If you are going to configure any inbound integration, you will want to add the integration URLs to your `urls.py`:
```python
from drf_integrations import integrations

urlpatterns = [
    ...
] + integrations.get_urls()
```

## Configuration
### Settings
DRF Integrations Framework relies on Django OAuth Toolkit to manage third party applications. In order to be able to use
it, first you'll need to configure DOT by setting (at least) the model references in your settings.
```python
OAUTH2_PROVIDER_APPLICATION_MODEL = "drf_integrations.Application"
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = "drf_integrations.AccessToken"
OAUTH2_PROVIDER_GRANT_MODEL = "drf_integrations.Grant"
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = "drf_integrations.RefreshToken"
```
Then, similarly, you will have to configure the model for the integrations.
```python
INTEGRATIONS_APPLICATION_INSTALLATION_MODEL = "drf_integrations.ApplicationInstallation"
```
You will also have to configure how the integrations are stored in the database. On the one hand, you will have to set
the type of JSON field your DB uses. On the other hand, you will have to set the name of the attribute where you want to
relate the integrations.
```python
DB_BACKEND_JSON_FIELD = "django.db.models.JSONField"
INTEGRATIONS_APPLICATION_INSTALLATION_INSTALL_ATTRIBUTE = "organisation"
```
Finally, you have to set the list of integrations that are available in your system (see the following section to learn
about creating integrations).
```python
INSTALLED_INTEGRATIONS = [
    "example.drf_integrations_example.api.integrations.APIClientIntegration",
]
```
### Creating integrations
An integration is represented by an extension of `BaseIntegration`. Then, the integration will be available to be
installed to different clients (as related with the previously configured
`INTEGRATIONS_APPLICATION_INSTALLATION_INSTALL_ATTRIBUTE`) once it is stored into an `Application`. This can be done in
two different ways:
1. Internal integrations (or non-local integrations) are those that can be configured once and installed to different clients with different
parameters. For example, your system may connect to Mixpanel, the connections and interactions with the service are all
the same, only the secret in the connection changes.

   These will only have 1 `Application` object in the database, and it can be related to multiple installations. They
   can also be automatically created by using the `syncregistry` management command.
   ```bash
   python manage.py syncregistry
   ```

1. Local integrations are those that are specific to just one client. For example, OAuth clients are local, there is
1 application per client, which will have the specific credentials for them, so they can only be installed once. These
are usually created on demand as required by clients.

An integration broadly has 3 functions:
1. Generates a list of URLs that a third party represented by this integration can connect to.
Mainly used for inward integrations.
1. Returns a client that can connect to the third party it represents. Mainly used for outward integrations.
1. Produce queryset filter lookups to search for installations of the integration.

Once you have a class inheriting from `BaseIntegration` that represents a third party, simply add it to
`INSTALLED_INTEGRATIONS` in your settings and the sky is the limit! You can create custom authentication backends,
permissions, event hooks... Take a look at [the example](example) to see some basic examples of how you can make use
of DRF Integrations Framework.

### Preconfigured
There are some features that DRF Integrations Framework provides out of the box.

- Admin model for `ApplicationInstallation` that already handles integration-specific configuration via dynamic forms.
- Automatic form validation for integrations that have one.
- An authentication backend for local OAuth2 integrations
(`drf_integrations.auth_backends.IntegrationOAuth2Authentication`).

## Running the tests

To run the tests you need to have a postgresql server running on localhost and have a
postgres user/role defined. To create the postgres user and role you can use the
following:

```psql -c 'CREATE ROLE postgres WITH LOGIN SUPERUSER' ```

To run the tests execute the following

```make tests```

If running tests under pycharm ensure that `python tests` -> `pytest` is used and set
the `Additional Arguments` to `--no-migrations`

Failing to specify `--no-migrations` will result in the following error:
```
ValueError: Related model 'oauth2_provider.idtoken' cannot be resolved
```

## Changelog
See [Releases](https://github.com/yoyowallet/drf-integrations-framework/releases)

## Authors
DRF Integrations Framework is an original idea by [@jianyuan](https://github.com/jianyuan), developed and maintained by
the loyalty domain team at [@saltpay](https://github.com/saltpay).
