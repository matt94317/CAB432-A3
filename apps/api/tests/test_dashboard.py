"""Campaign dashboard (US-19, US-20), creator performance (US-21) and who's behind
target (US-22). Pace rules are tested in packages/core/tests/test_progress.py; these
use campaigns where the outcome doesn't depend on the weekday."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

TODAY = datetime.now(ZoneInfo("Australia/Brisbane")).date()


@pytest.fixture
def lou(make_creator, alex):
    return make_creator(alex, "lou", email="lou@example.com")


@pytest.fixture
def amy(make_creator, alex):
    return make_creator(alex, "amy")


@pytest.fixture
def ended(make_campaign, assign, alex, lou, amy):
    """Ended yesterday, so the whole last period is due: Lou posts 2 of 2, Amy 0 of 2."""
    campaign = make_campaign(
        alex,
        name="Ended",
        start_date=(TODAY - timedelta(days=60)).isoformat(),
        end_date=(TODAY - timedelta(days=1)).isoformat(),
    )
    assign(alex, campaign, lou, amy, target_posts=2, target_period="month")
    return campaign


def add_post(client, headers, campaign, handle, n, on, **metrics):
    response = client.post(
        f"/api/campaigns/{campaign['id']}/posts",
        json={
            "url": f"https://www.tiktok.com/@{handle}/video/{100000 + n}",
            "posted_on": on.isoformat(),
            **metrics,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def dashboard(client, headers, campaign):
    return client.get(f"/api/campaigns/{campaign['id']}/dashboard", headers=headers)


def test_dashboard_shows_posts_vs_target_and_totals(client, alex, ended):
    last_day = TODAY - timedelta(days=1)
    add_post(client, alex, ended, "lou", 1, last_day, views=1000, likes=80, comments=15, shares=5)
    add_post(client, alex, ended, "lou", 2, last_day, views=500, likes=20)

    body = dashboard(client, alex, ended).json()

    amy_row, lou_row = body["creators"]  # behind first
    assert (amy_row["creator"]["handle"], amy_row["status"]) == ("amy", "behind")
    assert (amy_row["posts_this_period"], amy_row["remaining"]) == (0, 2)
    assert (lou_row["creator"]["handle"], lou_row["status"]) == ("lou", "met")
    assert lou_row["totals"]["views"] == 1500
    assert body["behind_count"] == 1

    totals = body["totals"]
    assert (totals["posts"], totals["views"], totals["engagement"]) == (2, 1500, 120)
    assert totals["engagement_rate"] == 0.08

    assert body["daily"][-1] == {
        "date": last_day.isoformat(),
        "posts": 2,
        "views": 1500,
        "engagement": 120,
    }
    assert len(body["daily"]) == 60
    assert body["last_synced_at"] is None  # nobody synced yet


def test_dashboard_is_cached_until_something_changes(client, alex, ended):
    assert dashboard(client, alex, ended).headers["X-Cache"] == "miss"
    cached = dashboard(client, alex, ended)
    assert cached.headers["X-Cache"] == "hit"
    assert cached.json()["totals"]["posts"] == 0

    add_post(client, alex, ended, "lou", 1, TODAY - timedelta(days=1))  # a write

    fresh = dashboard(client, alex, ended)
    assert fresh.headers["X-Cache"] == "miss"
    assert fresh.json()["totals"]["posts"] == 1


def test_failed_writes_and_other_organisations_dont_invalidate(client, login, alex, ended):
    dashboard(client, alex, ended)
    bad = client.post(f"/api/campaigns/{ended['id']}/posts", json={"url": "x"}, headers=alex)
    assert bad.status_code == 422
    client.post("/api/creators", json={"name": "S", "handle": "sams"}, headers=login("sam"))
    assert dashboard(client, alex, ended).headers["X-Cache"] == "hit"


def test_sync_refreshes_the_dashboard(client, tiktok, make_campaign, assign, alex, lou):
    live = make_campaign(alex, name="Live", tracking_hashtags=["lumiglow"])
    assign(alex, live, lou)
    dashboard(client, alex, live)
    tiktok.post("lou", "77", "#lumiglow", views=42)

    client.post(f"/api/campaigns/{live['id']}/sync", headers=alex)

    fresh = dashboard(client, alex, live)
    assert fresh.headers["X-Cache"] == "miss"
    assert fresh.json()["totals"]["views"] == 42
    assert fresh.json()["last_synced_at"] is not None


def test_behind_target_lists_live_campaigns_only(client, make_campaign, assign, alex, lou, ended):
    # Live campaign that started 3 weeks ago with a weekly target of 7: due daily
    live = make_campaign(
        alex,
        name="Live",
        start_date=(TODAY - timedelta(days=21)).isoformat(),
        end_date=(TODAY + timedelta(days=21)).isoformat(),
    )
    assign(alex, live, lou, target_posts=7)

    items = client.get("/api/behind-target", headers=alex).json()
    # "Ended" isn't live any more, so Amy isn't listed even though she missed it
    assert [(i["campaign_name"], i["creator"]["handle"]) for i in items] == [("Live", "lou")]
    assert items[0]["email"] == "lou@example.com"
    assert items[0]["expected_by_today"] >= 1


def test_creator_performance_across_campaigns(client, make_campaign, assign, alex, lou, ended):
    other = make_campaign(alex, name="Autumn")
    assign(alex, other, lou)
    add_post(client, alex, ended, "lou", 1, TODAY - timedelta(days=1), views=300)
    add_post(client, alex, other, "lou", 2, TODAY, views=700)

    body = client.get(f"/api/creators/{lou['id']}/performance", headers=alex).json()

    assert (body["totals"]["posts"], body["totals"]["views"]) == (2, 1000)
    by_name = {c["name"]: c for c in body["campaigns"]}
    # Ended yesterday with 1 of 2 monthly posts: the whole target was due
    assert (by_name["Ended"]["posts_this_period"], by_name["Ended"]["status"]) == (1, "behind")
    assert by_name["Ended"]["campaign_status"] == "active"
    assert by_name["Autumn"]["totals"]["views"] == 700
    assert [p["views"] for p in body["posts"]] == [700, 300]  # newest first


def test_other_organisations_get_not_found(client, login, alex, lou, ended):
    sam = login("sam")
    assert dashboard(client, sam, ended).status_code == 404
    assert client.get(f"/api/creators/{lou['id']}/performance", headers=sam).status_code == 404
    assert client.get("/api/behind-target", headers=sam).json() == []


def test_requires_login(client, ended):
    assert dashboard(client, {}, ended).status_code == 401
    assert client.get("/api/behind-target").status_code == 401


def test_generated_at_is_recent(client, alex, ended):
    generated = datetime.fromisoformat(dashboard(client, alex, ended).json()["generated_at"])
    assert datetime.now(UTC) - generated < timedelta(minutes=1)
