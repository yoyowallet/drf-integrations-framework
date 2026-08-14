from http import HTTPStatus

import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from oauth2_provider.models import ClientSecretField
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.settings import oauth2_settings

from drf_integrations import models
from tests import factories


class TestOAuthToolkitModelCompatibility:
    """Verify framework-owned OAuth models mirror DOT 2.4's abstract models.

    See https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html.
    """

    @pytest.mark.parametrize(
        ("model", "expected_fields"),
        [
            (
                models.Application,
                {
                    "algorithm",
                    "allowed_origins",
                    "hash_client_secret",
                    "post_logout_redirect_uris",
                },
            ),
            (models.Grant, {"claims", "nonce"}),
        ],
    )
    def test_required_fields_are_mirrored(self, model, expected_fields):
        """Assert each swapped model contains its cumulative DOT 2.4 fields."""
        # Given a framework-owned concrete OAuth model

        # When its complete field state is inspected
        actual_fields = {field.name for field in model._meta.get_fields()}

        # Then it contains every field added by DOT through 2.4
        assert expected_fields.issubset(actual_fields)

    def test_client_secret_uses_dot_hashing_field(self):
        """Ensure new and updated applications use DOT's hash-aware field.

        See the DOT ``ClientSecretField`` reference:
        https://django-oauth-toolkit.readthedocs.io/en/2.4.0/models.html#oauth2_provider.models.ClientSecretField.
        """
        # Given the framework's concrete OAuth application model

        # When the client secret field is inspected
        client_secret = models.Application._meta.get_field("client_secret")

        # Then DOT's hash-aware field implementation is used
        assert isinstance(client_secret, ClientSecretField)

    def test_access_token_has_oidc_relationship_and_token_index(self):
        """Verify the access-token OIDC relationship and 2.4 index state."""
        # Given the framework's concrete access-token model

        # When its DOT 2.4 relationship and token field are inspected
        id_token = models.AccessToken._meta.get_field("id_token")
        token = models.AccessToken._meta.get_field("token")

        # Then the OIDC relationship and lookup index match DOT 2.4
        assert id_token.one_to_one
        assert id_token.null
        assert token.db_index


@pytest.mark.django_db
class TestClientSecretStorage:
    """Verify secure storage semantics for fresh application writes."""

    @pytest.mark.parametrize("hash_client_secret", [True, False])
    def test_application_respects_hash_client_secret_setting(
        self, plaintext_client_secret, hash_client_secret
    ):
        """Store secrets according to the application's explicit hashing policy."""
        # Given a new application with an explicit secret-hashing policy
        application = factories.ApplicationFactory(
            client_secret=plaintext_client_secret,
            hash_client_secret=hash_client_secret,
        )

        # When the application is reloaded from persistent storage
        application.refresh_from_db()

        # Then its stored secret follows the configured hashing policy
        if hash_client_secret:
            assert application.client_secret != plaintext_client_secret
            assert check_password(plaintext_client_secret, application.client_secret)
        else:
            assert application.client_secret == plaintext_client_secret

    def test_recognised_django_hash_is_not_double_hashed(
        self, plaintext_client_secret, recognised_client_secret_hash
    ):
        """Preserve an existing recognized hash byte-for-byte on model save."""
        # Given an application created with an already hashed secret
        application = factories.ApplicationFactory(
            client_secret=recognised_client_secret_hash
        )

        # When the application is reloaded after DOT's field preparation
        application.refresh_from_db()

        # Then the hash is unchanged and still verifies the plaintext credential
        assert application.client_secret == recognised_client_secret_hash
        assert check_password(plaintext_client_secret, application.client_secret)


class TestClientSecretAuthentication:
    """Verify callers authenticate with plaintext, never the stored hash."""

    @pytest.mark.parametrize(
        ("credential_fixture", "is_valid"),
        [
            ("plaintext_client_secret", True),
            ("recognised_client_secret_hash", False),
            (None, False),
        ],
    )
    def test_only_original_plaintext_credential_is_accepted(
        self,
        request,
        recognised_client_secret_hash,
        credential_fixture,
        is_valid,
    ):
        """Accept only the original plaintext when validating a stored hash."""
        # Given a stored hash and a plaintext, hashed, or missing presented credential
        credential = (
            request.getfixturevalue(credential_fixture) if credential_fixture else ""
        )

        # When DOT validates the presented credential against the stored value
        is_secret_valid = OAuth2Validator()._check_secret(
            credential, recognised_client_secret_hash
        )

        # Then only the original plaintext credential authenticates
        assert is_secret_valid is is_valid


@pytest.mark.django_db
class TestOAuthClientCredentialsFlow:
    """Exercise client authentication through DOT's real token endpoint."""

    @pytest.mark.parametrize(
        ("credential_source", "expected_status"),
        [
            ("plaintext", HTTPStatus.OK),
            ("stored_hash", HTTPStatus.UNAUTHORIZED),
            ("incorrect", HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_token_endpoint_authenticates_only_original_secret(
        self,
        client,
        confidential_oauth_application,
        plaintext_client_secret,
        credential_source,
        expected_status,
    ):
        """Accept only the issued plaintext secret at DOT's real token endpoint."""
        # Given an approved client and one of the representative credentials
        credentials = {
            "plaintext": plaintext_client_secret,
            "stored_hash": confidential_oauth_application.client_secret,
            "incorrect": "incorrect-client-secret",
        }

        # When a client-credentials token is requested
        response = client.post(
            reverse("oauth2_provider:token"),
            data={
                "grant_type": "client_credentials",
                "client_id": confidential_oauth_application.client_id,
                "client_secret": credentials[credential_source],
            },
        )

        # Then only the original plaintext secret produces an access token
        assert response.status_code == expected_status
        if expected_status == HTTPStatus.OK:
            assert response.json()["access_token"]
            assert models.AccessToken.objects.filter(
                application=confidential_oauth_application,
                user__isnull=True,
            ).exists()


class TestPKCECompatibility:
    """Document and verify DOT 2.4's PKCE behavior by grant type.

    See https://django-oauth-toolkit.readthedocs.io/en/2.4.0/settings.html#pkce-required.
    """

    def test_pkce_is_required_by_default_for_authorization_code(self):
        """Confirm authorization-code clients inherit DOT 2.4's secure default.

        OAuthLib consults this validator hook for the authorization-code flow.
        Client credentials, password, refresh-token, and bearer validation flows do
        not issue authorization codes and therefore do not use a PKCE challenge.
        """
        # Given DOT 2.4's default OAuth provider settings

        # When the authorization-code validator checks the client
        pkce_required = OAuth2Validator().is_pkce_required("client-id", request=None)

        # Then PKCE is enabled and required for the authorization-code flow
        assert oauth2_settings.PKCE_REQUIRED is True
        assert pkce_required is True

    def test_framework_keeps_client_credentials_available_without_pkce(self):
        """Ensure the framework's grant override still permits client credentials."""
        # Given an application configured for the authorization-code grant
        application = models.Application(
            authorization_grant_type=models.Application.GRANT_AUTHORIZATION_CODE
        )

        # When the framework checks its additional client-credentials grant support
        client_credentials_allowed = application.allows_grant_type(
            models.Application.GRANT_CLIENT_CREDENTIALS
        )

        # Then client credentials remain available without a PKCE exchange
        assert client_credentials_allowed
