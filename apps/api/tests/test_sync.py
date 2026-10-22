"""Sync now (US-13) with hashtag matching (US-14), refreshed metrics (US-17) and
last-synced times (US-18). TikTok is the conftest FakeTikTok."""

import pytest


@pytest.fixture
def lou(make_creator, alex):
    return make_creator(alex, "lou")


@pytest.fixture
def summer(make_campaign, assign, alex, lou):
    campaign = make_campaign(alex, name="Summer", tracking_hashtags=["lumiglow"])
    assign(alex, campaign, lou)
    return campaign


def sync(client, headers, campaign):
    return client.post(f"/api/campaigns/{campaign['id']}/sync", headers=headers)


def test_sync_pulls_in_matching_posts(client, tiktok, alex, summer, lou):
    tiktok.post("lou", "1", "Morning routine #LumiGlow", views=500, likes=40)
    tiktok.post("lou", "2", "Unrelated #fyp")

    response = sync(client, alex, summer)
    run = response.json()
    assert response.status_code == 200
    assert (run["mode"], run["creators"], run["added"], run["updated"]) == ("inline", 1, 1, 0)
    assert run["failed"] == []

    [post] = client.get(f"/api/campaigns/{summer['id']}/posts", headers=alex).json()
    assert (post["views"], post["likes"], post["match_source"]) == (500, 40, "hashtag")
    assert post["last_synced_at"] is not None

    [row] = client.get(f"/api/campaigns/{summer['id']}/creators", headers=alex).json()
    assert row["creator"]["last_synced_at"] is not None


def test_resync_refreshes_metrics(client, tiktok, alex, summer):
    tiktok.post("lou", "1", "#lumiglow", views=500)
    sync(client, alex, summer)
    tiktok.posts["lou"] = []
    tiktok.post("lou", "1", "#lumiglow", views=900)

    run = sync(client, alex, summer).json()
    assert (run["added"], run["updated"]) == (0, 1)
    [post] = client.get(f"/api/campaigns/{summer['id']}/posts", headers=alex).json()
    assert post["views"] == 900


def test_removed_posts_stay_removed(client, tiktok, alex, summer):
    tiktok.post("lou", "1", "#lumiglow")
    sync(client, alex, summer)
    [post] = client.get(f"/api/campaigns/{summer['id']}/posts", headers=alex).json()
    client.delete(f"/api/posts/{post['id']}", headers=alex)

    sync(client, alex, summer)
    assert client.get(f"/api/campaigns/{summer['id']}/posts", headers=alex).json() == []


def test_one_failing_creator_doesnt_stop_the_rest(
    client, tiktok, make_creator, assign, alex, summer
):
    amy = make_creator(alex, "amy")
    assign(alex, summer, amy)
    tiktok.failing.add("lou")
    tiktok.post("amy", "5", "#lumiglow")

    run = sync(client, alex, summer).json()
    assert (run["creators"], run["added"]) == (1, 1)
    assert [(f["handle"], f["error"]) for f in run["failed"]] == [("lou", "TikTok is down")]


def test_nothing_to_sync_before_the_campaign_starts(
    client, tiktok, make_campaign, assign, alex, lou
):
    later = make_campaign(alex, start_date="2099-01-01", end_date="2099-02-01")
    assign(alex, later, lou)
    tiktok.post("lou", "1", "#lumiglow")
    assert sync(client, alex, later).json()["creators"] == 0


def test_archived_and_other_organisations_campaigns(client, login, alex, summer):
    assert sync(client, login("sam"), summer).status_code == 404
    client.post(f"/api/campaigns/{summer['id']}/archive", headers=alex)
    assert sync(client, alex, summer).status_code == 409


def test_queued_mode_publishes_one_job_per_creator(client, alex, summer, lou):
    from hookd_api.deps import get_sync_runner
    from hookd_api.main import app
    from hookd_api.services.sync import QueuedSync

    class FakePublisher:
        jobs = []

        def publish(self, jobs):
            self.jobs.extend(jobs)

    publisher = FakePublisher()
    app.dependency_overrides[get_sync_runner] = lambda: QueuedSync(publisher)

    run = sync(client, alex, summer).json()
    assert (run["mode"], run["creators"]) == ("queued", 1)
    assert [str(j.creator_id) for j in publisher.jobs] == [lou["id"]]


def test_sync_everything_syncs_each_live_creator_once(
    client, tiktok, make_campaign, make_creator, assign, alex, summer, lou
):
    other = make_campaign(alex, name="Autumn", tracking_hashtags=["autumn"])
    amy = make_creator(alex, "amy")
    assign(alex, other, lou, amy)  # lou is on two campaigns
    make_campaign(alex, name="Later", start_date="2099-01-01", end_date="2099-02-01")
    tiktok.post("lou", "1", "#lumiglow")
    tiktok.post("amy", "2", "#autumn")

    run = client.post("/api/sync", headers=alex).json()
    assert (run["creators"], run["added"]) == (2, 2)
    assert len(client.get("/api/posts", headers=alex).json()) == 2
