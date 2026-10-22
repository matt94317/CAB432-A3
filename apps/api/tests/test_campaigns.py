"""Campaign CRUD, archive and list (US-03 to US-06)."""

from datetime import UTC, datetime, timedelta

import pytest

TODAY = datetime.now(UTC).date()


def campaign_body(**overrides):
    body = {
        "name": "Summer Glow",
        "brand": "Lumi Skincare",
        "start_date": TODAY.isoformat(),
        "end_date": (TODAY + timedelta(days=30)).isoformat(),
        "tracking_hashtags": ["#LumiGlow", "summer24"],
    }
    return {**body, **overrides}


@pytest.fixture
def created(client, alex):
    response = client.post("/api/campaigns", json=campaign_body(), headers=alex)
    assert response.status_code == 201
    return response.json()


def test_requires_login(client):
    assert client.get("/api/campaigns").status_code == 401
    assert client.post("/api/campaigns", json=campaign_body()).status_code == 401


def test_create_campaign(created):
    assert created["name"] == "Summer Glow"
    assert created["brand"] == "Lumi Skincare"
    assert created["status"] == "active"
    assert created["phase"] == "live"
    assert created["tracking_hashtags"] == ["lumiglow", "summer24"]


def test_hashtags_are_normalised_and_deduplicated(client, alex):
    body = campaign_body(tracking_hashtags=[" #Glow ", "glow", "#GLOW", "skin_care"])
    response = client.post("/api/campaigns", json=body, headers=alex)
    assert response.json()["tracking_hashtags"] == ["glow", "skin_care"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"brand": ""},
        {"tracking_hashtags": []},
        {"tracking_hashtags": ["not a tag"]},
        {"tracking_hashtags": [f"tag{i}" for i in range(21)]},
        {"end_date": (TODAY - timedelta(days=1)).isoformat()},
    ],
    ids=["blank-name", "blank-brand", "no-hashtags", "bad-hashtag", "too-many", "end-before-start"],
)
def test_rejects_invalid_campaign(client, alex, overrides):
    response = client.post("/api/campaigns", json=campaign_body(**overrides), headers=alex)
    assert response.status_code == 422


def test_phase_follows_dates(client, alex):
    upcoming = campaign_body(
        start_date=(TODAY + timedelta(days=5)).isoformat(),
        end_date=(TODAY + timedelta(days=10)).isoformat(),
    )
    ended = campaign_body(
        start_date=(TODAY - timedelta(days=10)).isoformat(),
        end_date=(TODAY - timedelta(days=5)).isoformat(),
    )
    assert client.post("/api/campaigns", json=upcoming, headers=alex).json()["phase"] == "upcoming"
    assert client.post("/api/campaigns", json=ended, headers=alex).json()["phase"] == "ended"


def test_list_shows_only_my_campaigns(client, login, created):
    sam = login("sam")
    client.post("/api/campaigns", json=campaign_body(name="Sam's campaign"), headers=sam)

    alex_list = client.get("/api/campaigns", headers=login("alex")).json()
    sam_list = client.get("/api/campaigns", headers=sam).json()

    assert [c["name"] for c in alex_list] == ["Summer Glow"]
    assert [c["name"] for c in sam_list] == ["Sam's campaign"]
    assert alex_list[0]["progress"] is None


def test_other_organisations_campaign_is_not_found(client, login, created):
    sam = login("sam")
    url = f"/api/campaigns/{created['id']}"
    assert client.get(url, headers=sam).status_code == 404
    assert client.patch(url, json={"name": "Hijacked"}, headers=sam).status_code == 404
    assert client.post(f"{url}/archive", headers=sam).status_code == 404
    assert client.delete(url, headers=sam).status_code == 404


def test_get_campaign(client, alex, created):
    response = client.get(f"/api/campaigns/{created['id']}", headers=alex)
    assert response.status_code == 200
    assert response.json() == created


def test_update_campaign(client, alex, created):
    response = client.patch(
        f"/api/campaigns/{created['id']}",
        json={"name": "Summer Glow 2", "tracking_hashtags": ["#NewTag"]},
        headers=alex,
    )
    body = response.json()
    assert response.status_code == 200
    assert body["name"] == "Summer Glow 2"
    assert body["brand"] == "Lumi Skincare"  # unchanged
    assert body["tracking_hashtags"] == ["newtag"]


def test_update_rejects_end_before_existing_start(client, alex, created):
    response = client.patch(
        f"/api/campaigns/{created['id']}",
        json={"end_date": (TODAY - timedelta(days=1)).isoformat()},
        headers=alex,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "End date must be on or after the start date"


def test_archive_and_restore(client, alex, created):
    url = f"/api/campaigns/{created['id']}"

    archived = client.post(f"{url}/archive", headers=alex).json()
    assert archived["status"] == "archived"
    assert client.get("/api/campaigns", headers=alex).json() == []
    assert len(client.get("/api/campaigns?status=archived", headers=alex).json()) == 1
    assert len(client.get("/api/campaigns?status=all", headers=alex).json()) == 1

    # Archived campaigns are read-only
    assert client.patch(url, json={"name": "Nope"}, headers=alex).status_code == 409

    restored = client.post(f"{url}/restore", headers=alex).json()
    assert restored["status"] == "active"
    assert client.patch(url, json={"name": "Yes"}, headers=alex).status_code == 200


def test_delete_campaign(client, alex, created):
    url = f"/api/campaigns/{created['id']}"
    assert client.delete(url, headers=alex).status_code == 204
    assert client.get(url, headers=alex).status_code == 404
    assert client.delete(url, headers=alex).status_code == 404
