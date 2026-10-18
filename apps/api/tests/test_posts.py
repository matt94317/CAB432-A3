"""Manual post entry, move and remove (US-15, US-16), and a campaign's posts (US-17)."""

from datetime import UTC, datetime, timedelta

import pytest

TODAY = datetime.now(UTC).date()
LINK = "https://www.tiktok.com/@lou/video/7350000000000000001?is_from_webapp=1"


@pytest.fixture
def lou(make_creator, alex):
    return make_creator(alex, "lou")


@pytest.fixture
def summer(make_campaign, assign, alex, lou):
    campaign = make_campaign(alex, name="Summer", tracking_hashtags=["lumiglow"])
    assign(alex, campaign, lou)
    return campaign


@pytest.fixture
def autumn(make_campaign, assign, alex, lou):
    campaign = make_campaign(alex, name="Autumn", tracking_hashtags=["autumn"])
    assign(alex, campaign, lou)
    return campaign


def add(client, headers, campaign, url=LINK, **body):
    return client.post(
        f"/api/campaigns/{campaign['id']}/posts",
        json={"url": url, "posted_on": TODAY.isoformat(), **body},
        headers=headers,
    )


def posts_in(client, headers, campaign):
    return client.get(f"/api/campaigns/{campaign['id']}/posts", headers=headers).json()


def test_add_post_by_link(client, alex, summer, lou):
    response = add(client, alex, summer, caption="Glow #LumiGlow #ad", views=1200, likes=90)
    post = response.json()
    assert response.status_code == 201
    assert post["url"] == "https://www.tiktok.com/@lou/video/7350000000000000001"
    assert post["creator"]["id"] == lou["id"]
    assert post["match_source"] == "manual"
    assert post["hashtags"] == ["lumiglow", "ad"]
    assert (post["views"], post["likes"], post["comments"]) == (1200, 90, 0)
    assert post["last_synced_at"] is None
    assert [p["id"] for p in posts_in(client, alex, summer)] == [post["id"]]


@pytest.mark.parametrize(
    "url",
    [
        "tiktok.com/@Lou/video/7350000000000000001",
        "https://m.tiktok.com/@lou/video/7350000000000000001/",
        "https://www.tiktok.com/@lou/photo/7350000000000000001",
    ],
)
def test_link_formats(client, alex, summer, url):
    assert add(client, alex, summer, url=url).status_code == 201


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("https://vm.tiktok.com/ZMabc123/", "Short links"),
        ("https://www.instagram.com/p/abc", "Paste a TikTok post link"),
        ("https://www.tiktok.com/@lou", "Paste a TikTok post link"),
    ],
)
def test_rejects_bad_links(client, alex, summer, url, message):
    response = add(client, alex, summer, url=url)
    assert response.status_code == 422
    assert message in response.json()["detail"][0]["msg"]


def test_rejects_posts_from_creators_not_on_the_campaign(client, make_creator, alex, summer):
    make_creator(alex, "amy")  # in the roster, but not assigned
    for handle in ("amy", "stranger"):
        response = add(client, alex, summer, url=f"https://www.tiktok.com/@{handle}/video/123456")
        assert response.status_code == 422
        assert response.json()["detail"] == f"@{handle} isn't assigned to Summer"


def test_rejects_future_dates_and_negative_metrics(client, alex, summer):
    future = (TODAY + timedelta(days=3)).isoformat()
    assert add(client, alex, summer, posted_on=future).status_code == 422
    assert add(client, alex, summer, views=-1).status_code == 422


def test_same_post_cant_be_tracked_twice(client, alex, summer, autumn):
    add(client, alex, summer)
    response = add(client, alex, autumn)
    assert response.status_code == 409
    assert response.json()["detail"] == "This post is already tracked in Summer. Move it instead."


def test_move_post(client, alex, summer, autumn):
    post = add(client, alex, summer).json()
    response = client.patch(
        f"/api/posts/{post['id']}", json={"campaign_id": autumn["id"]}, headers=alex
    )
    assert response.status_code == 200
    assert response.json()["campaign_id"] == autumn["id"]
    assert posts_in(client, alex, summer) == []
    assert len(posts_in(client, alex, autumn)) == 1


def test_move_needs_the_creator_on_the_destination(client, make_campaign, alex, summer):
    elsewhere = make_campaign(alex, name="Elsewhere")
    post = add(client, alex, summer).json()
    response = client.patch(
        f"/api/posts/{post['id']}", json={"campaign_id": elsewhere["id"]}, headers=alex
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "@lou isn't assigned to Elsewhere"


def test_remove_post_then_add_it_back(client, alex, summer):
    post = add(client, alex, summer).json()
    assert client.delete(f"/api/posts/{post['id']}", headers=alex).status_code == 204
    assert posts_in(client, alex, summer) == []
    assert client.delete(f"/api/posts/{post['id']}", headers=alex).status_code == 404

    again = add(client, alex, summer)
    assert again.status_code == 201
    assert again.json()["id"] == post["id"]


def test_archived_campaign_posts_are_read_only(client, alex, summer, autumn):
    post = add(client, alex, summer).json()
    client.post(f"/api/campaigns/{summer['id']}/archive", headers=alex)

    assert add(client, alex, summer, url=LINK.replace("01?", "02?")).status_code == 409
    move = {"campaign_id": autumn["id"]}
    assert client.patch(f"/api/posts/{post['id']}", json=move, headers=alex).status_code == 409
    assert client.delete(f"/api/posts/{post['id']}", headers=alex).status_code == 409
    assert len(posts_in(client, alex, summer)) == 1


def test_progress_counts_posts_this_period_up_to_each_target(
    client, make_creator, assign, alex, summer
):
    amy = make_creator(alex, "amy")
    assign(alex, summer, amy, target_posts=2)
    for i in range(3):  # Lou posts 3 against a target of 3
        add(client, alex, summer, url=f"https://www.tiktok.com/@lou/video/10000{i}")
    for i in range(4):  # Amy posts 4 against 2; the extra 2 don't cover for anyone
        add(client, alex, summer, url=f"https://www.tiktok.com/@amy/video/20000{i}")

    progress = client.get("/api/campaigns", headers=alex).json()[0]["progress"]
    assert progress == {"creators": 2, "posts": 5, "target_posts": 5, "behind": 0}


def test_cascades(client, alex, summer, autumn, lou):
    add(client, alex, summer)
    add(client, alex, autumn, url="https://www.tiktok.com/@lou/video/999999")

    # Unassigning removes the creator's posts in that campaign only
    client.delete(f"/api/campaigns/{summer['id']}/creators/{lou['id']}", headers=alex)
    assert posts_in(client, alex, summer) == []
    assert len(posts_in(client, alex, autumn)) == 1

    # Removing the creator removes the rest
    client.delete(f"/api/creators/{lou['id']}", headers=alex)
    assert posts_in(client, alex, autumn) == []


def test_other_organisations_posts_are_not_found(client, login, alex, summer):
    post = add(client, alex, summer).json()
    sam = login("sam")
    assert client.get(f"/api/campaigns/{summer['id']}/posts", headers=sam).status_code == 404
    assert add(client, sam, summer).status_code == 404
    move = {"campaign_id": summer["id"]}
    assert client.patch(f"/api/posts/{post['id']}", json=move, headers=sam).status_code == 404
    assert client.delete(f"/api/posts/{post['id']}", headers=sam).status_code == 404
