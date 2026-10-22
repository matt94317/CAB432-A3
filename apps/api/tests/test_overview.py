"""Workspace overview: totals vs last month, performance, to-dos, live campaigns and
standout creators."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

TODAY = datetime.now(ZoneInfo("Australia/Brisbane")).date()
MONTH_START = TODAY.replace(day=1)
LAST_MONTH_START = (MONTH_START - timedelta(days=1)).replace(day=1)


def overview(client, headers, **params):
    return client.get("/api/overview", params=params, headers=headers)


@pytest.fixture
def lou(make_creator, alex):
    return make_creator(alex, "lou")


@pytest.fixture
def amy(make_creator, alex):
    return make_creator(alex, "amy")


@pytest.fixture
def live(make_campaign, assign, alex, lou, amy):
    """Live since before last month, so posts from both months can be added to it."""
    campaign = make_campaign(
        alex,
        name="Everyday",
        start_date=(LAST_MONTH_START - timedelta(days=5)).isoformat(),
        end_date=(TODAY + timedelta(days=40)).isoformat(),
    )
    assign(alex, campaign, lou, amy, target_posts=2, target_period="month")
    return campaign


def add_post(client, headers, campaign, handle, n, on, views=0, likes=0):
    response = client.post(
        f"/api/campaigns/{campaign['id']}/posts",
        json={
            "url": f"https://www.tiktok.com/@{handle}/video/{100000 + n}",
            "posted_on": on.isoformat(),
            "views": views,
            "likes": likes,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def test_empty_workspace(client, alex):
    body = overview(client, alex).json()
    assert body["month"] == f"{TODAY.year}-{TODAY.month:02d}"
    assert body["comparing"] == "same_days"
    assert (body["period_start"], body["period_end"]) == (
        MONTH_START.isoformat(),
        TODAY.isoformat(),
    )
    assert body["totals"]["posts"] == 0
    assert body["needs_attention"] == []
    assert body["active_campaigns"] == []
    assert body["next_milestone"] is None
    assert body["standout_creators"] == []
    assert len(body["daily"]) == TODAY.day


def test_month_to_date_vs_the_same_days_last_month(client, alex, live):
    add_post(client, alex, live, "lou", 1, TODAY, views=300, likes=30)
    add_post(client, alex, live, "amy", 2, LAST_MONTH_START, views=100)
    # Last month, but after the same number of days: not in the comparison
    late_last_month = MONTH_START - timedelta(days=1)
    if (late_last_month - LAST_MONTH_START).days >= TODAY.day:
        add_post(client, alex, live, "amy", 3, late_last_month, views=999)

    body = overview(client, alex).json()
    assert (body["totals"]["posts"], body["totals"]["views"]) == (1, 300)
    assert body["totals"]["engagement_rate"] == 0.1
    assert (body["previous"]["posts"], body["previous"]["views"]) == (1, 100)
    assert body["compare_start"] == LAST_MONTH_START.isoformat()
    assert body["active_creators"] == 2
    assert body["new_creators"] == 2  # both first assigned this month
    # previous_daily covers the whole of last month for the chart
    assert body["previous_daily"][0]["views"] == 100


def test_past_month_compares_full_months(client, alex, live):
    add_post(client, alex, live, "lou", 1, LAST_MONTH_START + timedelta(days=2), views=50)
    month = f"{LAST_MONTH_START.year}-{LAST_MONTH_START.month:02d}"
    body = overview(client, alex, month=month).json()
    assert body["comparing"] == "full_month"
    assert body["period_end"] == (MONTH_START - timedelta(days=1)).isoformat()
    assert body["totals"]["views"] == 50
    assert body["new_creators"] == 0


@pytest.mark.parametrize("month", ["2026", "2026-13", "October", "2026-1-1"])
def test_rejects_bad_months(client, alex, month):
    assert overview(client, alex, month=month).status_code == 422


def test_needs_attention(client, make_campaign, make_creator, assign, alex):
    behind = make_campaign(
        alex,
        name="Daily",
        start_date=(TODAY - timedelta(days=21)).isoformat(),
        end_date=(TODAY + timedelta(days=3)).isoformat(),
    )
    make_campaign(alex, name="Empty", end_date=(TODAY + timedelta(days=30)).isoformat())
    assign(alex, behind, make_creator(alex, "lou"), target_posts=7)  # a post a day, none made

    items = overview(client, alex).json()["needs_attention"]
    kinds = [(i["kind"], i["title"]) for i in items]
    assert kinds == [
        ("behind", "1 creator behind target"),
        ("ending_soon", "Daily wraps in 3 days"),
        ("no_creators", "No creators on Empty"),
        ("not_synced", "1 creator not synced yet"),
    ]
    assert items[0]["campaign_id"] == behind["id"]


def test_active_campaigns_and_milestone(client, make_campaign, assign, alex, lou, live):
    sooner = make_campaign(alex, name="Sooner", end_date=(TODAY + timedelta(days=5)).isoformat())
    assign(alex, sooner, lou, target_posts=3)
    make_campaign(  # upcoming: not live
        alex,
        name="Later",
        start_date=(TODAY + timedelta(days=10)).isoformat(),
        end_date=(TODAY + timedelta(days=20)).isoformat(),
    )
    body = overview(client, alex).json()
    rows = body["active_campaigns"]
    assert [r["name"] for r in rows] == ["Sooner", "Everyday"]
    assert (rows[1]["creators"], rows[1]["target_posts"]) == (2, 4)
    assert body["next_milestone"]["name"] == "Sooner"


def test_standout_creators_by_views(client, make_creator, assign, alex, lou, amy, live):
    ben = make_creator(alex, "ben")
    zed = make_creator(alex, "zed")
    assign(alex, live, ben, zed)
    for n, (handle, views) in enumerate([("lou", 10), ("amy", 500), ("ben", 200), ("zed", 50)]):
        add_post(client, alex, live, handle, n, TODAY, views=views)

    standouts = overview(client, alex).json()["standout_creators"]
    assert [(s["handle"], s["views"]) for s in standouts] == [
        ("amy", 500),
        ("ben", 200),
        ("zed", 50),
    ]


def test_cached_until_something_changes(client, alex, live):
    assert overview(client, alex).headers["X-Cache"] == "miss"
    assert overview(client, alex).headers["X-Cache"] == "hit"
    add_post(client, alex, live, "lou", 1, TODAY, views=5)
    fresh = overview(client, alex)
    assert fresh.headers["X-Cache"] == "miss"
    assert fresh.json()["totals"]["views"] == 5


def test_only_my_organisation(client, login, alex, live):
    add_post(client, alex, live, "lou", 1, TODAY, views=5)
    sam = overview(client, login("sam")).json()
    assert sam["totals"]["posts"] == 0
    assert sam["active_campaigns"] == []


def test_requires_login(client):
    assert client.get("/api/overview").status_code == 401
