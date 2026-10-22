"""Tests for hashtag matching (US-14)."""

import uuid
from datetime import date

from hookd_core.matching import extract_hashtags, match_campaign, normalise_hashtags
from hookd_core.repositories.campaigns import Campaign

ORG = uuid.uuid4()


def campaign(name, tags, start=date(2026, 10, 1), end=date(2026, 10, 31)):
    return Campaign(
        organisation_id=ORG,
        name=name,
        brand="Brand",
        start_date=start,
        end_date=end,
        tracking_hashtags=tuple(tags),
    )


def test_extract_hashtags():
    assert extract_hashtags("Glow up #LumiGlow #ad #lumiglow, #skin_care!") == (
        "lumiglow",
        "ad",
        "skin_care",
    )
    assert extract_hashtags("no tags here") == ()


def test_normalise_platform_hashtags():
    assert normalise_hashtags(["LumiGlow", "#ad", " ", "lumiglow"]) == ("lumiglow", "ad")


def test_matches_on_any_tracking_hashtag_within_dates():
    summer = campaign("Summer", ["lumiglow", "summer24"])
    assert match_campaign(["fyp", "summer24"], date(2026, 10, 5), [summer]) is summer
    assert match_campaign(["fyp"], date(2026, 10, 5), [summer]) is None


def test_campaign_dates_are_inclusive():
    summer = campaign("Summer", ["lumiglow"])
    assert match_campaign(["lumiglow"], date(2026, 10, 1), [summer]) is summer
    assert match_campaign(["lumiglow"], date(2026, 10, 31), [summer]) is summer
    assert match_campaign(["lumiglow"], date(2026, 9, 30), [summer]) is None
    assert match_campaign(["lumiglow"], date(2026, 11, 1), [summer]) is None


def test_most_shared_hashtags_wins():
    broad = campaign("Broad", ["lumi"])
    specific = campaign("Specific", ["lumi", "glowserum"])
    assert match_campaign(["lumi", "glowserum"], date(2026, 10, 5), [broad, specific]) is specific


def test_tie_goes_to_the_most_recent_campaign():
    older = campaign("Older", ["lumi"], start=date(2026, 9, 1))
    newer = campaign("Newer", ["lumi"], start=date(2026, 10, 1))
    assert match_campaign(["lumi"], date(2026, 10, 5), [newer, older]) is newer
    assert match_campaign(["lumi"], date(2026, 10, 5), [older, newer]) is newer
