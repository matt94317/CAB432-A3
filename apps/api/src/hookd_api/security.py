"""Cognito authentication (US-01, US-02).

The web app sends the Cognito *access* token as a Bearer token. We verify its
signature against the user pool's JWKS and check issuer, expiry, token_use and
client_id. Access tokens carry no profile data, so on a user's first request we
read their email and name from Cognito's GetUser API.
"""

from dataclasses import dataclass
from typing import Any, Protocol

import boto3
import jwt


class AuthError(Exception):
    """The token is missing, malformed, expired or not issued for this app."""


class SigningKeySource(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: str
    username: str


@dataclass(frozen=True)
class CognitoProfile:
    email: str
    name: str


def region_from_pool_id(user_pool_id: str) -> str:
    # Pool ids look like "ap-southeast-2_AbC123"
    return user_pool_id.split("_", 1)[0]


class CognitoTokenVerifier:
    def __init__(
        self,
        user_pool_id: str,
        app_client_id: str,
        key_source: SigningKeySource | None = None,
    ) -> None:
        region = region_from_pool_id(user_pool_id)
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self.app_client_id = app_client_id
        self._keys = key_source or jwt.PyJWKClient(
            f"{self.issuer}/.well-known/jwks.json", cache_keys=True
        )

    def verify(self, token: str) -> AccessTokenClaims:
        try:
            signing_key = self._keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"require": ["exp", "iat", "iss", "sub", "token_use", "client_id"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthError(str(exc)) from exc

        if claims["token_use"] != "access":
            raise AuthError("Expected an access token")
        if claims["client_id"] != self.app_client_id:
            raise AuthError("Token was issued for a different app client")

        return AccessTokenClaims(sub=claims["sub"], username=claims.get("username", claims["sub"]))


def fetch_cognito_profile(access_token: str, user_pool_id: str) -> CognitoProfile:
    """Read the signed-in user's attributes from Cognito (GetUser needs no IAM credentials)."""
    client = boto3.client("cognito-idp", region_name=region_from_pool_id(user_pool_id))
    response = client.get_user(AccessToken=access_token)
    attributes = {a["Name"]: a["Value"] for a in response["UserAttributes"]}
    email = attributes.get("email", "")
    return CognitoProfile(email=email, name=attributes.get("name") or email.split("@")[0])
