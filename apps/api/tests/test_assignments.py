"""Assign creators to campaigns, set and change targets, unassign (US-09 to US-12)."""

import pytest


@pytest.fixture
def campaign(make_campaign, alex):
    return make_campaign(alex)


@pytest.fixture
def lou(make_creator, alex):
    return make_creator(alex, "lou")


@pytest.fixture
def amy(make_creator, alex):
    return make_creator(alex, "amy")


def test_assign_creators_with_a_target(client, alex, campaign, lou, amy, assign):
    response = assign(alex, campaign, lou, amy, target_posts=4, target_period="month")
    assert response.status_code == 201
    assigned = response.json()
    assert [a["creator"]["handle"] for a in assigned] == ["lou", "amy"]
    assert all(a["target_posts"] == 4 and a["target_period"] == "month" for a in assigned)

    listed = client.get(f"/api/campaigns/{campaign['id']}/creators", headers=alex).json()
    assert [a["creator"]["handle"] for a in listed] == ["amy", "lou"]  # by name


def test_duplicate_ids_in_one_request_are_assigned_once(client, alex, campaign, lou, assign):
    response = assign(alex, campaign, lou, lou)
    assert response.status_code == 201
    assert len(response.json()) == 1


def test_assigning_twice_is_a_conflict_and_assigns_nobody(client, alex, campaign, lou, amy, assign):
    assign(alex, campaign, lou)
    response = assign(alex, campaign, amy, lou)
    assert response.status_code == 409
    assert response.json()["detail"] == "Already assigned to this campaign: @lou"
    listed = client.get(f"/api/campaigns/{campaign['id']}/creators", headers=alex).json()
    assert [a["creator"]["handle"] for a in listed] == ["lou"]


@pytest.mark.parametrize(
    "body",
    [
        {"creator_ids": [], "target_posts": 3, "target_period": "week"},
        {"target_posts": 0, "target_period": "week"},
        {"target_posts": 101, "target_period": "week"},
        {"target_posts": 3, "target_period": "fortnight"},
    ],
    ids=["no-creators", "zero-target", "huge-target", "bad-period"],
)
def test_rejects_invalid_assignment(client, alex, campaign, lou, body):
    body = {"creator_ids": [lou["id"]], **body}
    response = client.post(f"/api/campaigns/{campaign['id']}/creators", json=body, headers=alex)
    assert response.status_code == 422


def test_campaign_list_shows_progress(client, alex, campaign, lou, amy, assign):
    assert client.get("/api/campaigns", headers=alex).json()[0]["progress"] is None
    assign(alex, campaign, lou, target_posts=3)
    assign(alex, campaign, amy, target_posts=2)
    progress = client.get("/api/campaigns", headers=alex).json()[0]["progress"]
    assert progress == {"creators": 2, "posts": 0, "target_posts": 5}


def test_creator_shows_their_campaigns(client, alex, make_campaign, campaign, lou, assign):
    other = make_campaign(alex, name="Autumn")
    assign(alex, campaign, lou, target_posts=3, target_period="week")
    assign(alex, other, lou, target_posts=8, target_period="month")

    assert client.get(f"/api/creators/{lou['id']}", headers=alex).json()["campaign_count"] == 2
    assert client.get("/api/creators", headers=alex).json()[0]["campaign_count"] == 2

    rows = client.get(f"/api/creators/{lou['id']}/campaigns", headers=alex).json()
    assert [(r["name"], r["target_posts"], r["target_period"]) for r in rows] == [
        ("Autumn", 8, "month"),
        ("Summer Glow", 3, "week"),
    ]


def test_change_target(client, alex, campaign, lou, assign):
    assign(alex, campaign, lou, target_posts=3, target_period="week")
    url = f"/api/campaigns/{campaign['id']}/creators/{lou['id']}"

    response = client.patch(url, json={"target_posts": 10}, headers=alex)
    assert response.status_code == 200
    assert (response.json()["target_posts"], response.json()["target_period"]) == (10, "week")

    response = client.patch(url, json={"target_period": "month"}, headers=alex)
    assert (response.json()["target_posts"], response.json()["target_period"]) == (10, "month")

    assert client.patch(url, json={}, headers=alex).status_code == 422


def test_targets_are_per_campaign(client, alex, make_campaign, campaign, lou, assign):
    other = make_campaign(alex, name="Autumn")
    assign(alex, campaign, lou, target_posts=3)
    assign(alex, other, lou, target_posts=3)
    client.patch(
        f"/api/campaigns/{campaign['id']}/creators/{lou['id']}",
        json={"target_posts": 9},
        headers=alex,
    )
    other_row = client.get(f"/api/campaigns/{other['id']}/creators", headers=alex).json()[0]
    assert other_row["target_posts"] == 3


def test_change_target_of_unassigned_creator_is_not_found(client, alex, campaign, lou):
    url = f"/api/campaigns/{campaign['id']}/creators/{lou['id']}"
    assert client.patch(url, json={"target_posts": 2}, headers=alex).status_code == 404


def test_unassign_keeps_creator_in_roster(client, alex, campaign, lou, assign):
    assign(alex, campaign, lou)
    url = f"/api/campaigns/{campaign['id']}/creators/{lou['id']}"
    assert client.delete(url, headers=alex).status_code == 204
    assert client.get(f"/api/campaigns/{campaign['id']}/creators", headers=alex).json() == []
    assert client.get(f"/api/creators/{lou['id']}", headers=alex).status_code == 200
    assert client.delete(url, headers=alex).status_code == 404
    # And they can be assigned again
    assert assign(alex, campaign, lou).status_code == 201


def test_archived_campaign_is_read_only(client, alex, campaign, lou, amy, assign):
    assign(alex, campaign, lou)
    client.post(f"/api/campaigns/{campaign['id']}/archive", headers=alex)
    url = f"/api/campaigns/{campaign['id']}/creators/{lou['id']}"

    assert assign(alex, campaign, amy).status_code == 409
    assert client.patch(url, json={"target_posts": 5}, headers=alex).status_code == 409
    assert client.delete(url, headers=alex).status_code == 409
    # Still readable
    assert len(client.get(f"/api/campaigns/{campaign['id']}/creators", headers=alex).json()) == 1


def test_deleting_a_campaign_removes_its_assignments(client, alex, campaign, lou, assign):
    assign(alex, campaign, lou)
    client.delete(f"/api/campaigns/{campaign['id']}", headers=alex)
    assert client.get(f"/api/creators/{lou['id']}", headers=alex).json()["campaign_count"] == 0


def test_removing_a_creator_removes_their_assignments(client, alex, campaign, lou, amy, assign):
    assign(alex, campaign, lou, amy)
    client.delete(f"/api/creators/{lou['id']}", headers=alex)
    listed = client.get(f"/api/campaigns/{campaign['id']}/creators", headers=alex).json()
    assert [a["creator"]["handle"] for a in listed] == ["amy"]


def test_cannot_touch_other_organisations(
    client, login, make_campaign, make_creator, alex, lou, assign
):
    sam = login("sam")
    sams_campaign = make_campaign(sam)
    my_campaign = make_campaign(alex)

    # Can't put my creator on Sam's campaign, or Sam's creator on mine
    assert assign(alex, sams_campaign, lou).status_code == 404
    assert assign(alex, my_campaign, make_creator(sam, "sams")).status_code == 404

    assign(alex, my_campaign, lou)
    url = f"/api/campaigns/{my_campaign['id']}/creators"
    assert client.get(url, headers=sam).status_code == 404
    assert (
        client.patch(f"{url}/{lou['id']}", json={"target_posts": 1}, headers=sam).status_code == 404
    )
    assert client.delete(f"{url}/{lou['id']}", headers=sam).status_code == 404
