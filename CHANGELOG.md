# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.6.2] - 2022-04-09
### Changed
- Adds init_form_data hook to perform additional actions when ApplicationInstallationForm initialised.

## [0.6.1] - 2021-04-13
### Changed
- Fix ApplicationInstallationForm to allow empty incoming config values

## [0.6.0] - 2021-04-12
### Changed
- Allow an `Application` to be standalone without an integration to allow direct usage of the `ApplicationInstallation` config field.

## [0.5.0] - 2021-01-27
### Added
- Allow an `ApplicationInstallation` model object's `config` field to be [`blank`](https://docs.djangoproject.com/en/3.0/ref/models/fields/#blank).

## [0.4.0] - 2020-09-08
### Added
- Add `namespace` property to `BaseIntegration` class.

## [0.3.0] - 2020-08-14
### Added
- Add optional var-positional `implements` parameter to `Registry.get_all`.
- Add var-keyword argument `**kwargs` to `BaseIntegration.get_installation_lookup_from_request`

### Changed
- **Backwards-incompatible**: Change the `application` argument of `BaseIntegration.get_installation_lookup_from_request` to be keyword-only.


## [0.2.0] - 2020-08-03
### Added
- Add support for django-oauth-toolkit >= 1.3.0

### Changed
- **Backwards-incompatible** [django-oauth-toolkit squashed migrations](
https://github.com/jazzband/django-oauth-toolkit/blob/master/CHANGELOG.md#130-2020-03-02): If you are currently on a
release < 1.2.0, you will need to first install 1.2.0 then manage.py migrate before upgrading to >= 1.3.0.

### Removed
- Remove support for django-oauth-toolkit < 1.3.0


## [0.1.0] - 2020-06-25
### Added
- This CHANGELOG file to hopefully serve as an evolving example of a
  standardized open source project CHANGELOG.
- An example and basic guidelines.
- README links to CHANGELOG.
