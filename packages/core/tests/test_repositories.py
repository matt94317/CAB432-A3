"""Repository contract: the in-memory and DynamoDB stores must behave the same.

DynamoDB runs on moto, so no AWS account or local DynamoDB is needed.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_aws

from hookd_core.enums import CampaignStatus, MatchSource, Platform, TargetPeriod
from hookd_core.repositories.assignments import Assignment
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.creators import Creator
from hookd_core.repositories.dynamodb import _Table
from hookd_core.repositories.posts import Post
from hookd_core.repositories.users import Organisation, User
from hookd_core.storage import make_storage

ORG = uuid.uuid4()
OTHER_ORG = uuid.uuid4()
NOW = datetime(2026, 10, 18, 9, 30, tzinfo=UTC)


@pytest.fixture(params=["memory", "dynamodb"])
def storage(request, monkeypatch):
    if request.param == "memory":
        yield make_storage("memory")
        return
    for var in ("AWS_ENDPOINT_URL", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield make_storage("dynamodb", table_name="hookd-test", create_table=True)


@pytest.fixture
def stores(storage):
    return storage.stores


def campaign(org=ORG, **overrides):
    return Campaign(
        organisation_id=org,
        name=overrides.pop("name", "Summer"),
        brand="Lumi",
        start_date=overrides.pop("start_date", date(2026, 10, 1)),
        end_date=date(2026, 10, 31),
        tracking_hashtags=("lumiglow", "summer24"),
        **overrides,
    )


def creator(org=ORG, handle="lou", **overrides):
    return Creator(organisation_id=org, name=handle.title(), handle=handle, **overrides)


def assignment(campaign_id, creator_id, org=ORG):
    return Assignment(org, campaign_id, creator_id, target_posts=3, target_period=TargetPeriod.WEEK)


def post(creator_id, campaign_id, external_id="1", org=ORG, **overrides):
    return Post(
        organisation_id=org,
        creator_id=creator_id,
        campaign_id=campaign_id,
        external_id=external_id,
        url=f"https://www.tiktok.com/@lou/video/{external_id}",
        posted_at=overrides.pop("posted_at", NOW),
        match_source=overrides.pop("match_source", MatchSource.HASHTAG),
        **overrides,
    )


# --- Campaigns ---


def test_campaign_round_trip_and_scoping(stores):
    saved = stores.campaigns.add(campaign(status=CampaignStatus.ARCHIVED))
    assert stores.campaigns.get(ORG, saved.id) == saved
    assert stores.campaigns.get(OTHER_ORG, saved.id) is None


def test_campaign_list_filters_and_sorts(stores):
    old = stores.campaigns.add(campaign(name="Old", start_date=date(2026, 1, 1)))
    new = stores.campaigns.add(campaign(name="New"))
    archived = stores.campaigns.add(campaign(name="Gone", status=CampaignStatus.ARCHIVED))
    stores.campaigns.add(campaign(org=OTHER_ORG))

    assert [c.id for c in stores.campaigns.list(ORG, CampaignStatus.ACTIVE)] == [new.id, old.id]
    assert {c.id for c in stores.campaigns.list(ORG)} == {old.id, new.id, archived.id}


def test_campaign_save_and_delete(stores):
    saved = stores.campaigns.add(campaign())
    updated = stores.campaigns.save(saved.__class__(**{**saved.__dict__, "name": "Renamed"}))
    assert stores.campaigns.get(ORG, saved.id).name == "Renamed"
    assert updated.updated_at >= saved.updated_at
    assert stores.campaigns.delete(OTHER_ORG, saved.id) is False
    assert stores.campaigns.delete(ORG, saved.id) is True
    assert stores.campaigns.delete(ORG, saved.id) is False


# --- Creators ---


def test_creator_round_trip_with_optional_fields(stores):
    full = stores.creators.add(
        creator(niche="Skincare", email="lou@example.com", phone="+61", last_synced_at=NOW)
    )
    bare = stores.creators.add(creator(handle="amy"))
    assert stores.creators.get(ORG, full.id) == full
    assert stores.creators.get(ORG, bare.id) == bare
    assert bare.niche is None


def test_creator_by_handle_and_list(stores):
    lou = stores.creators.add(creator(handle="lou"))
    amy = stores.creators.add(creator(handle="amy"))
    stores.creators.add(creator(org=OTHER_ORG, handle="lou"))

    assert stores.creators.get_by_handle(ORG, Platform.TIKTOK, "lou") == lou
    assert stores.creators.get_by_handle(ORG, Platform.TIKTOK, "nobody") is None
    assert [c.id for c in stores.creators.list(ORG)] == [amy.id, lou.id]


# --- Assignments ---


def test_assignments(stores):
    summer, autumn = uuid.uuid4(), uuid.uuid4()
    lou, amy = uuid.uuid4(), uuid.uuid4()
    stores.assignments.add_many(
        [assignment(summer, lou), assignment(summer, amy), assignment(autumn, lou)]
    )
    stores.assignments.add_many([assignment(uuid.uuid4(), uuid.uuid4(), org=OTHER_ORG)])

    got = stores.assignments.get(ORG, summer, lou)
    assert (got.campaign_id, got.creator_id, got.target_period) == (summer, lou, TargetPeriod.WEEK)
    assert stores.assignments.get(OTHER_ORG, summer, lou) is None
    assert len(stores.assignments.list(ORG)) == 3
    assert {a.creator_id for a in stores.assignments.list(ORG, campaign_id=summer)} == {lou, amy}
    assert {a.campaign_id for a in stores.assignments.list(ORG, creator_id=lou)} == {summer, autumn}
    assert len(stores.assignments.list_all()) == 4  # every organisation

    assert stores.assignments.delete_where(ORG, creator_id=lou) == 2
    assert [a.creator_id for a in stores.assignments.list(ORG)] == [amy]
    assert stores.assignments.delete(ORG, summer, amy) is True
    assert stores.assignments.list(ORG) == []


def test_assignment_save_keeps_it_in_the_fan_out_index(stores):
    a = stores.assignments.add_many([assignment(uuid.uuid4(), uuid.uuid4())])[0]
    stores.assignments.save(a.__class__(**{**a.__dict__, "target_posts": 9}))
    [listed] = stores.assignments.list_all()
    assert listed.target_posts == 9


# --- Posts ---


def test_post_round_trip(stores):
    full = post(
        uuid.uuid4(),
        uuid.uuid4(),
        caption="Glow #lumiglow",
        hashtags=("lumiglow",),
        views=12_345_678_901,
        likes=5,
        last_synced_at=NOW,
        match_source=MatchSource.MANUAL,
    )
    stores.posts.add(full)
    assert stores.posts.get(ORG, full.id) == full
    assert stores.posts.get(OTHER_ORG, full.id) is None


def test_post_ids_come_from_the_natural_key(stores):
    lou, summer = uuid.uuid4(), uuid.uuid4()
    first = stores.posts.add(post(lou, summer, views=1))
    again = stores.posts.save(post(lou, summer, views=2))  # same video, synced again
    assert first.id == again.id
    assert [p.views for p in stores.posts.list(ORG)] == [2]
    assert stores.posts.get_by_external_id(ORG, lou, Platform.TIKTOK, "1").views == 2
    assert stores.posts.get_by_external_id(ORG, lou, Platform.TIKTOK, "2") is None


def test_post_list_hides_removed_posts_but_lookup_finds_them(stores):
    lou, summer, autumn = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    stores.posts.add(post(lou, summer, "1", posted_at=NOW - timedelta(days=1)))
    stores.posts.add(post(lou, summer, "2", posted_at=NOW))
    stores.posts.add(post(lou, autumn, "3"))
    stores.posts.add(post(lou, summer, "4", removed=True))

    assert [p.external_id for p in stores.posts.list(ORG, campaign_id=summer)] == ["2", "1"]
    assert len(stores.posts.list(ORG, creator_id=lou)) == 3
    assert stores.posts.get_by_external_id(ORG, lou, Platform.TIKTOK, "4").removed is True

    # delete_where includes removed posts
    assert stores.posts.delete_where(ORG, campaign_id=summer, creator_id=lou) == 3
    assert [p.external_id for p in stores.posts.list(ORG)] == ["3"]


# --- Users ---


def test_user_create_and_race(storage):
    org = Organisation(name="Alex's organisation")
    alex = User(organisation_id=org.id, name="Alex", email="a@example.com", cognito_sub="sub-1")
    assert storage.users.create(alex, org) == alex
    assert storage.users.get_by_cognito_sub("sub-1") == alex
    assert storage.users.get_by_cognito_sub("sub-2") is None

    # A second first-request for the same Cognito user gets the existing user
    other_org = Organisation(name="Duplicate")
    duplicate = User(
        organisation_id=other_org.id, name="Alex", email="a@x.com", cognito_sub="sub-1"
    )
    assert storage.users.create(duplicate, other_org) == alex


# --- DynamoDB specifics ---


def test_dynamodb_queries_follow_pagination(storage):
    if not hasattr(storage.stores.campaigns, "_t"):
        pytest.skip("DynamoDB only")
    for i in range(5):
        storage.stores.campaigns.add(campaign(name=f"C{i}"))
    table = _Table(storage.stores.campaigns._t.table)
    items = list(table._paginate(KeyConditionExpression=Key("pk").eq(f"ORG#{ORG}"), Limit=2))
    assert len(items) == 5
