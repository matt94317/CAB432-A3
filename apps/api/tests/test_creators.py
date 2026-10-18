"""Creator roster CRUD (US-07, US-08)."""

import pytest


def test_requires_login(client):
    assert client.get("/api/creators").status_code == 401
    assert client.post("/api/creators", json={"name": "A", "handle": "ab"}).status_code == 401


def test_add_creator(client, alex):
    body = {
        "name": "Lou Lumi",
        "handle": "@Lumi.Lou",
        "niche": " Skincare ",
        "email": "Lou@Example.com",
        "phone": "+61 400 000 000",
    }
    response = client.post("/api/creators", json=body, headers=alex)
    created = response.json()
    assert response.status_code == 201
    assert created["handle"] == "lumi.lou"
    assert created["platform"] == "tiktok"
    assert created["profile_url"] == "https://www.tiktok.com/@lumi.lou"
    assert created["niche"] == "Skincare"
    assert created["email"] == "lou@example.com"
    assert created["campaign_count"] == 0


def test_handle_can_be_a_profile_link(make_creator, alex):
    created = make_creator(alex, "https://www.tiktok.com/@Lumi.Lou?lang=en")
    assert created["handle"] == "lumi.lou"


def test_optional_fields_can_be_blank(client, alex):
    body = {"name": "Lou", "handle": "lou", "niche": "", "email": "  ", "phone": None}
    created = client.post("/api/creators", json=body, headers=alex).json()
    assert (created["niche"], created["email"], created["phone"]) == (None, None, None)


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "  "},
        {"handle": "a"},
        {"handle": "has space"},
        {"handle": "x" * 25},
        {"email": "not-an-email"},
        {"niche": "n" * 81},
    ],
    ids=["blank-name", "short-handle", "bad-handle", "long-handle", "bad-email", "long-niche"],
)
def test_rejects_invalid_creator(client, alex, overrides):
    body = {"name": "Lou", "handle": "lou", **overrides}
    assert client.post("/api/creators", json=body, headers=alex).status_code == 422


def test_handle_is_unique_in_my_roster(client, login, make_creator, alex):
    make_creator(alex, "lou")
    response = client.post("/api/creators", json={"name": "Lou 2", "handle": "@LOU"}, headers=alex)
    assert response.status_code == 409
    assert response.json()["detail"] == "@lou is already in your roster"
    # Another organisation can track the same creator
    make_creator(login("sam"), "lou")


def test_list_is_mine_and_sorted_by_name(client, login, make_creator, alex):
    make_creator(alex, "zed", name="Zed")
    make_creator(alex, "amy", name="amy", niche="Fitness")
    make_creator(login("sam"), "sams_creator")

    names = [c["name"] for c in client.get("/api/creators", headers=alex).json()]
    assert names == ["amy", "Zed"]


@pytest.mark.parametrize(
    ("search", "expected"), [("ZE", ["Zed"]), ("@amy", ["amy"]), ("fit", ["amy"])]
)
def test_search(client, make_creator, alex, search, expected):
    make_creator(alex, "zed", name="Zed")
    make_creator(alex, "amy", name="amy", niche="Fitness")
    found = client.get("/api/creators", params={"search": search}, headers=alex).json()
    assert [c["name"] for c in found] == expected


def test_edit_creator(client, make_creator, alex):
    creator = make_creator(alex, "lou", niche="Skincare", email="lou@example.com")
    response = client.patch(
        f"/api/creators/{creator['id']}",
        json={"handle": "@lou_new", "niche": None},
        headers=alex,
    )
    body = response.json()
    assert response.status_code == 200
    assert body["handle"] == "lou_new"
    assert body["niche"] is None  # cleared
    assert body["email"] == "lou@example.com"  # unchanged
    assert body["name"] == "Lou"


def test_edit_rejects_clearing_required_fields(client, make_creator, alex):
    creator = make_creator(alex, "lou")
    url = f"/api/creators/{creator['id']}"
    assert client.patch(url, json={"name": None}, headers=alex).status_code == 422
    assert client.patch(url, json={"handle": None}, headers=alex).status_code == 422


def test_edit_rejects_a_handle_already_in_roster(client, make_creator, alex):
    make_creator(alex, "taken")
    creator = make_creator(alex, "lou")
    url = f"/api/creators/{creator['id']}"
    assert client.patch(url, json={"handle": "taken"}, headers=alex).status_code == 409
    # Keeping its own handle is fine
    assert client.patch(url, json={"handle": "lou", "name": "Lou"}, headers=alex).status_code == 200


def test_other_organisations_creator_is_not_found(client, login, make_creator, alex):
    creator = make_creator(alex, "lou")
    sam = login("sam")
    url = f"/api/creators/{creator['id']}"
    assert client.get(url, headers=sam).status_code == 404
    assert client.patch(url, json={"name": "Hijacked"}, headers=sam).status_code == 404
    assert client.delete(url, headers=sam).status_code == 404
    assert client.get(f"{url}/campaigns", headers=sam).status_code == 404


def test_remove_creator(client, make_creator, alex):
    creator = make_creator(alex, "lou")
    url = f"/api/creators/{creator['id']}"
    assert client.delete(url, headers=alex).status_code == 204
    assert client.get(url, headers=alex).status_code == 404
    assert client.get("/api/creators", headers=alex).json() == []
    assert client.delete(url, headers=alex).status_code == 404
