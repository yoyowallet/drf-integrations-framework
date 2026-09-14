# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-14

This release modernizes the supported Python and Django versions and upgrades Django
OAuth Toolkit from the 1.4 line to the 2.4 line. It also brings the framework's custom
OAuth models and migrations in line with Django OAuth Toolkit 2.4.

### Added

- Support for Python 3.10 through 3.13 and Django 4.2 through 5.2.
- The fields introduced by Django OAuth Toolkit 2.4 on the framework-owned models:
  - `Application.algorithm`, `allowed_origins`, `hash_client_secret`, and
    `post_logout_redirect_uris`;
  - the OpenID Connect hybrid authorization grant type;
  - `AccessToken.id_token`;
  - `Grant.claims` and `nonce`.
- Migrations for both new installations and existing databases upgrading from the
  previous OAuth Toolkit integration.
- Coverage for model state, migrations, client-secret authentication, token
  endpoints, and PKCE behavior.
- An [OAuth Toolkit 2.4 upgrade and recovery guide][upgrade-guide].

### Changed

- Django OAuth Toolkit is now a runtime dependency with a supported range of
  `>=2.4,<3.0` instead of the previous 1.3–1.4 range. See the
  [Django OAuth Toolkit 2.4 release notes][dot-changelog].
- The minimum supported Python version is now 3.10 and the minimum supported Django
  version is now 4.2.
- OAuth application client secrets are stored using Django OAuth Toolkit's
  [hash-aware client-secret field][dot-client-secret].
- PKCE is required by default for the authorization-code flow, matching Django OAuth
  Toolkit 2.4.
- Migration ordering now ensures that Django OAuth Toolkit's concrete `IDToken` model
  is created after the configured application model is available.
- The build and development setup now uses the current Poetry build backend, Ruff for
  linting and formatting, expanded pre-commit checks, and an updated CI test matrix.

### Breaking changes

> [!WARNING]
> Python 3.9 and earlier and Django 3.2 and earlier are no longer supported. Projects
> on those versions must upgrade their runtime before installing this release.

> [!WARNING]
> Applying migration `0008_hash_existing_application_client_secrets` replaces
> existing plaintext client secrets with one-way hashes. The original value cannot be
> recovered from the database afterward, and reversing the migration does not restore
> it. Take and test an encrypted database backup before upgrading.

> [!WARNING]
> OAuth clients must continue sending the original plaintext secret. The value stored
> in `Application.client_secret` after migration is a hash and will not work as a
> credential. Ensure every active client secret is already held in an appropriate
> secret-management system; rotate any secret that cannot be recovered.

> [!WARNING]
> Authorization-code clients must now send a PKCE challenge and verifier. Existing
> clients that do not support PKCE will fail authorization unless the application
> deliberately configures a temporary override while those clients are migrated.

> [!WARNING]
> Projects that swap any OAuth Toolkit model must create matching migrations for their
> concrete models. The framework cannot alter a table owned by another Django app, so
> its client-secret data migration intentionally does nothing when `Application` is
> swapped.

### Side effects and upgrade notes

- Existing plaintext secrets are hashed only when `hash_client_secret=True`. Values
  already recognized as Django password hashes are preserved to avoid double hashing.
- Rolling application code back to Django OAuth Toolkit 1.4 after secrets have been
  hashed may prevent affected clients from authenticating. A full rollback requires
  restoring the pre-upgrade database backup as well as the previous package versions.
- Newly created or rotated client secrets are only available as plaintext at creation
  time. Capture and distribute them securely before the model is saved.
- PKCE affects the authorization-code flow only. Client credentials, password, refresh
  token, and bearer-token validation flows do not perform a PKCE exchange.
- `Application`, `AccessToken`, and `Grant` receive new schema fields during migration.
  Plan for the normal table locks and deployment time associated with schema changes
  on the size and database engine used by the consuming project.
- The legacy `setup.py` and `setup.cfg` files have been removed; packaging now uses
  `pyproject.toml` and Poetry.

[dot-changelog]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/changelog.html
[dot-client-secret]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html#oauth2_provider.models.ClientSecretField
[upgrade-guide]: docs/oauth-toolkit-2.4-upgrade.md

## [0.9.0a1] - 2025-09-05 - Pre Release Alpha1

### Added

- Support for Python 3.9 to 3.13
- Support for Django 3.2, 4.2, 5.2
- Changelog to track future changes.
- Pre-commit checks and run them as part of the Github actions workflow.
- Pre-commit checks for missing migrations
- Make file contains command db-setup to test running all migrations on an empty database

### Changed

- Use Ruff as linter

### Deprecated

- None

### Removed

- Dropped support for Django 2.2 and python 3.7 & 3.8

### Fixed

- None

### Security

- None

## [0.8.6] - 2023-05-02

### Added

- Added support for Python 3.11
- Added support for Django 4.2

## Changed

- Minor version updates to some packages
- Allow a wider range of Pillow versions

### Deprecated

- None

### Removed

- Drop support for Python 3.6

### Fixed

- Fixed issue with the form if the user only has view permissions.

### Security

- None

## [0.8.2] - 2022-05-05

### Added

- Adds migrations for `BigAuto` fields to conform to Django 4.* requirements.

## Changed

- None

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.8.1] - 2022-05-03

### Added

- Add support for Django 4.0.

## Changed

- Upgrade imported libraries to latest versions compatible with Python 3.7 and above.

### Deprecated

None

### Removed

- support for Python 3.6.

### Fixed

- None

### Security

- None

## [0.6.1] - 2021-04-15

### Added

- None

## Changed

- None

### Deprecated

- None

### Removed

- None

### Fixed

- Fixes ApplicationInstallationForm to allow empty incoming config values

### Security

- None

## [0.6.0] - 2021-04-12

### Added

- None

## Changed

- Support installations without integrations

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.5.0] - 2021-01-27

### Added

- Add migrations to make config blank
- Add release notes for new version

## Changed

- Allow ApplicationInstallation config to be blank

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.4.0] - 2020-09-08

### Added

- Add namespace property to BaseIntegration class.

## Changed

- None

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.3.0] - 2020-08-17

### Added

- Add optional var-positional implements parameter to Registry.get_all.
- Add var-keyword argument **kwargs to BaseIntegration.get_installation_lookup_from_request

## Changed

- Backwards-incompatible: Change the application argument of BaseIntegration.get_installation_lookup_from_request to be keyword-only.

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.2.0] - 2020-08-03

### Added

- None

## Changed

- Bump OAuth toolkit to 1.3.0

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None

## [0.1.0] - 2020-07-08

### Added

- Initial release

## Changed

- None

### Deprecated

- None

### Removed

- None

### Fixed

- None

### Security

- None
