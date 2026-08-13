# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Mirrored cumulative [Django OAuth Toolkit 2.4.0 model changes][dot-models] for
  the framework-owned `Application`, `AccessToken`, and `Grant` models.
- Added fresh-database, existing-database, model-state, client-secret, token endpoint,
  and PKCE compatibility coverage.
- Added an operational upgrade and recovery guide for projects depending on this
  framework.

### Changed

- Raised the supported Django OAuth Toolkit range from 1.3–1.4 to `>=2.4,<2.5`;
  consumers should review the [DOT 2.4 release notes][dot-changelog].
- Declared fresh-install migration ordering so DOT's concrete `IDToken` is created
  only after the configured application model is available in migration state.
- New OAuth applications now inherit DOT 2.4's default behavior of storing
  [hashed client secrets][dot-client-secret].
- Authorization-code clients now inherit DOT 2.4's
  [`PKCE_REQUIRED=True` default][dot-pkce].

### Removed

- Dropped support for Python 3.9, which reached end of life in October 2025.
- Dropped support for Django 3.2, which reached end of extended support in April
  2024. The minimum supported Django version is now 4.2.

### Security

- Existing plaintext OAuth application secrets are one-way hashed during migration.
- Existing values recognized by Django's configured password hashers are preserved
  byte-for-byte, preventing double hashing.
- Client authentication is tested to accept the original plaintext credential and to
  reject the stored hash as a credential.

### Migration warning

- One-way secret hashing cannot be reversed by rolling back the migration. Take an
  encrypted database backup before deployment and retain original client credentials
  in the appropriate secret-management system. See
  [the upgrade guide](docs/oauth-toolkit-2.4-upgrade.md) for recovery steps.

[dot-changelog]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/changelog.html
[dot-client-secret]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html#oauth2_provider.models.ClientSecretField
[dot-models]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html
[dot-pkce]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/settings.html#pkce-required

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
