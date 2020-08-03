"""
As the original oauth2_provider models are overwritten and users are forced to inherit from
the new models here in drf_integrations, every migration in oauth2_provider must be
replicated here, and it has to be added as a dependency to the migration.

For example, migration 0002 here has as a dependency the migration 0001 here and
the migration 0002 from oauth2_provider.
"""
