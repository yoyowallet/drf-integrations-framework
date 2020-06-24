"""
As the original oauth2_provider models are overwritten and users are forced to inherit from
the new models here in drf_integrations, every migration in oauth2_provider must be
replicated here, and it has to be added as a dependency to the migration.

For example, migration 0002 here has as a dependency the migration 0001 here and
the migration 0002 from oauth2_provider.

There are also some additional checks to support oauth2_provider versions under 1.3.0, as
migrations were squashed then. These additional checks might be dropped in the future when
support for django-oauth-toolkit (oauth2_provider) < 1.3.0 is dropped.
"""
