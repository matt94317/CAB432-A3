"""GET /api/me: authentication and first-login provisioning (US-01, US-02)."""

from hookd_api.security import CognitoProfile


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_requires_token(client):
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_rejects_invalid_token(client, make_token):
    response = client.get("/api/me", headers=auth(make_token(token_use="id")))
    assert response.status_code == 401


def test_first_request_provisions_user_and_organisation(client, profiles, make_token):
    token = make_token(sub="sub-alex")
    profiles[token] = CognitoProfile(email="alex@example.com", name="Alex")

    response = client.get("/api/me", headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "alex@example.com"
    assert body["name"] == "Alex"
    assert body["organisation_id"]


def test_later_requests_reuse_the_same_user(client, profiles, make_token):
    first = make_token(sub="sub-alex")
    profiles[first] = CognitoProfile(email="alex@example.com", name="Alex")
    created = client.get("/api/me", headers=auth(first)).json()

    # A refreshed token for the same Cognito user must not hit Cognito again
    second = make_token(sub="sub-alex", iat=1)
    again = client.get("/api/me", headers=auth(second)).json()

    assert again == created
    assert second not in profiles


def test_each_user_gets_a_private_organisation(client, profiles, make_token):
    alex = make_token(sub="sub-alex")
    sam = make_token(sub="sub-sam")
    profiles[alex] = CognitoProfile(email="alex@example.com", name="Alex")
    profiles[sam] = CognitoProfile(email="sam@example.com", name="Sam")

    alex_me = client.get("/api/me", headers=auth(alex)).json()
    sam_me = client.get("/api/me", headers=auth(sam)).json()

    assert alex_me["id"] != sam_me["id"]
    assert alex_me["organisation_id"] != sam_me["organisation_id"]
