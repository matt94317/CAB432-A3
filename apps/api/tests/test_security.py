"""Cognito access-token verification."""

import time

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from hookd_api.security import AuthError, region_from_pool_id


def test_valid_access_token(verifier, make_token):
    claims = verifier.verify(make_token(sub="abc"))
    assert claims.sub == "abc"


@pytest.mark.parametrize(
    "overrides",
    [
        {"token_use": "id"},
        {"client_id": "another-app"},
        {"iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/other-pool"},
        {"exp": int(time.time()) - 10},
    ],
    ids=["id-token", "wrong-client", "wrong-issuer", "expired"],
)
def test_rejects_invalid_claims(verifier, make_token, overrides):
    with pytest.raises(AuthError):
        verifier.verify(make_token(**overrides))


def test_rejects_token_signed_by_another_key(verifier, make_token):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthError):
        verifier.verify(make_token(private_key=other_key))


def test_rejects_garbage(verifier):
    with pytest.raises(AuthError):
        verifier.verify("not-a-jwt")


def test_region_from_pool_id():
    assert region_from_pool_id("ap-southeast-2_AbC123") == "ap-southeast-2"
