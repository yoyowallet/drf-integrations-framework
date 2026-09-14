# Django OAuth Toolkit 2.4 upgrade guide

This release moves the framework from Django OAuth Toolkit (DOT) 1.4.x to the 2.4.x
line. It mirrors the cumulative schema of DOT's abstract `Application`, `AccessToken`,
`RefreshToken`, and `Grant` models while continuing to use DOT's concrete `IDToken`.
Read the upstream [DOT 2.4.0 release notes][dot-changelog] before upgrading; they call
out the irreversible client-secret migration and the PKCE default as breaking changes.

## Schema and behavior changes

The framework migrations add the following state from the
[DOT 2.4 model definitions][dot-models]:

- `Application.algorithm`, `allowed_origins`, `hash_client_secret`, and
  `post_logout_redirect_uris`;
- the OpenID hybrid authorization grant choice;
- DOT's [`ClientSecretField`][dot-client-secret] for `Application.client_secret`;
- `AccessToken.id_token` and the explicit token index;
- `Grant.claims` and `nonce`.

Migration `0007_oauth_toolkit_2_4_schema` applies the schema state after DOT's complete
`0010` migration chain. Migration `0008_hash_existing_application_client_secrets`
then converts unhashed legacy secrets. Keeping schema and data operations separate
makes the irreversible operation explicit and ensures it runs through the hash-aware
field state.

## Critical security and recovery warning

Hashing a plaintext client secret is intentionally irreversible. Reversing migration
`0008` is a no-op because a hash cannot be converted back to its original credential.
A code rollback to DOT 1.4 may also stop hashed clients authenticating because the old
validator does not provide DOT 2.4's plaintext-against-hash check.

Before production deployment:

1. Take an encrypted, access-controlled database snapshot using the normal production
   backup mechanism. Verify restoration in a non-production environment.
2. Confirm every active client still has its original plaintext credential in its
   owner-controlled secret store. Do not export plaintext secrets into logs, tickets,
   source control, or an unencrypted migration file.
3. Test a restored production-like database by migrating from framework `0006` through
   `0008`, then authenticate representative authorization-code and client-credentials
   clients with their original plaintext credentials.
4. Inventory clients by non-secret identifiers such as application primary key and
   `client_id`. Never use the stored `client_secret` hash as an outbound credential.
5. Deploy the dependency, framework migration, and owning-project concrete migrations
   together during a monitored change window.

If rollback is required after `0008`:

1. Stop writes and application traffic that can mutate OAuth applications.
2. Restore the pre-upgrade encrypted database snapshot.
3. Restore the previous framework and DOT package versions.
4. Reconcile any legitimate writes made after the snapshot before reopening traffic.

If no usable backup or original plaintext credential exists, the hash cannot recover
the secret. Rotate the affected client secret and distribute the replacement through
the approved secret-delivery process.

The data migration is atomic on databases that support transactional DDL. It uses the
migration connection's database alias, skips applications with
`hash_client_secret=False`, preserves hashes recognized by Django's configured
password hashers exactly, and hashes only unrecognized values. It deliberately becomes
a no-op when the framework `Application` is swapped; the owning project must perform
the equivalent operation on its concrete table.

## Impact on projects with swapped concrete models

This repository owns the abstract definitions and default concrete models. A consuming
project that configures models such as `login.Application`, `login.AccessToken`,
`login.RefreshToken`, or `login.Grant` must add matching concrete migrations in that
project. Framework operations for a swapped model update framework migration state but
do not alter the consumer's physical table.

For each consuming project:

1. Set all five model settings explicitly, including:

   ```python
   OAUTH2_PROVIDER_ID_TOKEN_MODEL = "oauth2_provider.IDToken"
   ```

2. Generate and review concrete migrations for all swapped models. They should include
   the fields listed above but should not create another `IDToken` unless the project
   deliberately swaps that model too.
3. Verify the migration graph on both an existing database and an empty database. DOT
   `0004` creates `IDToken` with a foreign key to the configured application model, so
   the consumer's concrete application must exist in migration state before DOT
   `0004`. Add deliberate `run_before` or dependency ordering in the owning project
   when necessary.
4. Reproduce the idempotent secret data migration on the physical concrete application
   table. This project cannot safely mutate a table owned by another Django app.
5. Run `makemigrations --check --dry-run` and the consumer's full migrated test suite.

Platform-specific concrete `login` model changes are intentionally outside this
repository and belong to ENTNERO-6023.

## Client authentication semantics

For the default `hash_client_secret=True` behavior:

- create or rotate the application with a plaintext secret;
- capture that plaintext value before saving or from the system that generated it;
- store only the generated hash in `Application.client_secret`;
- present the original plaintext value to the token endpoint;
- never copy the stored hash into a client configuration.

DOT 2.4's validator uses Django `check_password` for recognized stored hashes and a
constant-time comparison for deliberately unhashed secrets. The latter remains
available through `hash_client_secret=False`, but should be an explicit compatibility
decision rather than the default. DOT's [client-credentials example][dot-client-flow]
shows how the original issued secret is presented to the token endpoint.

## PKCE by grant type

DOT 2.4 changes the default [`OAUTH2_PROVIDER["PKCE_REQUIRED"]`][dot-pkce] value to
`True`. DOT's [authorization-code example][dot-authorization-code] demonstrates the
required challenge and verifier exchange.

| Flow | PKCE relevance | Required action |
| --- | --- | --- |
| Authorization code | Required by default | Send a code challenge during authorization and its verifier during token exchange. |
| Client credentials | Not applicable | Continue authenticating with client ID and original plaintext client secret. |
| Password | Not applicable | No PKCE challenge is issued; consider whether this legacy grant should remain enabled. |
| Refresh token | Not applicable to refresh exchange | Continue using the refresh token and configured client authentication. |
| Bearer validation | Not applicable | No client authorization code is issued. |

Projects needing a staged authorization-code rollout can configure a callable that
returns whether PKCE is required for a given client ID. A global `False` restores the
old behavior but weakens protection for every authorization-code client and should be
temporary, documented, and monitored.

## Upstream references

- [DOT 2.4.0 release notes][dot-changelog]
- [DOT 2.4 model reference][dot-models]
- [DOT 2.4 settings reference][dot-settings]
- [DOT authorization-code and client-credentials guide][dot-grants]
- [OAuth 2.0 PKCE specification (RFC 7636)][rfc-7636]

[dot-authorization-code]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/getting_started.html#authorization-code
[dot-changelog]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/changelog.html
[dot-client-flow]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/getting_started.html#client-credential
[dot-client-secret]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html#oauth2_provider.models.ClientSecretField
[dot-grants]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/getting_started.html#oauth2-authorization-grants
[dot-models]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html
[dot-pkce]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/settings.html#pkce-required
[dot-settings]: https://django-oauth-toolkit.readthedocs.io/en/2.4.0/settings.html
[rfc-7636]: https://www.rfc-editor.org/rfc/rfc7636
