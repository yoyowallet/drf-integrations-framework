from django.contrib.auth.hashers import check_password, make_password
from oauth2_provider.models import ClientSecretField
from oauth2_provider.oauth2_validators import OAuth2Validator

from drf_integrations import models


def test_oauth_24_model_state_is_mirrored():
    application_fields = {
        field.name: field for field in models.Application._meta.get_fields()
    }
    assert {
        "algorithm",
        "allowed_origins",
        "hash_client_secret",
        "post_logout_redirect_uris",
    }.issubset(application_fields)
    assert isinstance(application_fields["client_secret"], ClientSecretField)

    access_token_fields = {
        field.name: field for field in models.AccessToken._meta.get_fields()
    }
    assert access_token_fields["id_token"].one_to_one
    assert access_token_fields["id_token"].null
    assert access_token_fields["token"].db_index

    grant_fields = {field.name for field in models.Grant._meta.get_fields()}
    assert {"claims", "nonce"}.issubset(grant_fields)


def test_new_application_hashes_client_secret(db):
    application = models.Application.objects.create(
        client_id="new-client",
        client_secret="original-plaintext-secret",
        client_type=models.Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=models.Application.GRANT_CLIENT_CREDENTIALS,
    )

    application.refresh_from_db()

    assert application.client_secret != "original-plaintext-secret"
    assert check_password("original-plaintext-secret", application.client_secret)


def test_recognised_django_hash_is_not_double_hashed(db):
    existing_hash = make_password("original-plaintext-secret")

    application = models.Application.objects.create(
        client_id="already-hashed-client",
        client_secret=existing_hash,
        client_type=models.Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=models.Application.GRANT_CLIENT_CREDENTIALS,
    )

    application.refresh_from_db()

    assert application.client_secret == existing_hash


def test_client_authentication_requires_original_plaintext_secret():
    stored_hash = make_password("original-plaintext-secret")
    validator = OAuth2Validator()

    assert validator._check_secret("original-plaintext-secret", stored_hash)
    assert not validator._check_secret(stored_hash, stored_hash)

