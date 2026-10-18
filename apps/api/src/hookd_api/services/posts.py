"""Manual post entry, move and remove (US-15, US-16), and a campaign's posts (US-17)."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta, tzinfo

from hookd_api.errors import Conflict, InvalidRequest, NotFound
from hookd_api.schemas.post import PostCreate, PostCreator, PostMove, PostRead, post_url_parts
from hookd_api.services import campaigns as campaigns_service
from hookd_api.services.campaigns import CampaignArchived
from hookd_core.enums import CampaignStatus, MatchSource, Platform
from hookd_core.matching import extract_hashtags
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.creators import Creator
from hookd_core.repositories.posts import Post
from hookd_core.sync import Stores


class PostNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("Post not found")


class AlreadyTracked(Conflict):
    def __init__(self, campaign_name: str) -> None:
        super().__init__(f"This post is already tracked in {campaign_name}. Move it instead.")


class NotAssigned(InvalidRequest):
    def __init__(self, handle: str, campaign_name: str) -> None:
        super().__init__(f"@{handle} isn't assigned to {campaign_name}")


def to_read(post: Post, creator: Creator) -> PostRead:
    return PostRead(
        id=post.id,
        campaign_id=post.campaign_id,
        creator=PostCreator(id=creator.id, name=creator.name, handle=creator.handle),
        platform=post.platform,
        url=post.url,
        caption=post.caption,
        hashtags=list(post.hashtags),
        posted_at=post.posted_at,
        views=post.views,
        likes=post.likes,
        comments=post.comments,
        shares=post.shares,
        match_source=post.match_source,
        last_synced_at=post.last_synced_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _editable(stores: Stores, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign:
    campaign = campaigns_service.get(stores.campaigns, organisation_id, campaign_id)
    if campaign.status == CampaignStatus.ARCHIVED:
        raise CampaignArchived
    return campaign


def _read(stores: Stores, post: Post) -> PostRead:
    creator = stores.creators.get(post.organisation_id, post.creator_id)
    if creator is None:
        raise PostNotFound
    return to_read(post, creator)


def _get(stores: Stores, organisation_id: uuid.UUID, post_id: uuid.UUID) -> Post:
    post = stores.posts.get(organisation_id, post_id)
    if post is None or post.removed:
        raise PostNotFound
    return post


def list_for_campaign(
    stores: Stores, organisation_id: uuid.UUID, campaign_id: uuid.UUID
) -> list[PostRead]:
    """The campaign's posts, newest first."""
    campaigns_service.get(stores.campaigns, organisation_id, campaign_id)
    creators = {c.id: c for c in stores.creators.list(organisation_id)}
    return [
        to_read(p, creators[p.creator_id])
        for p in stores.posts.list(organisation_id, campaign_id=campaign_id)
        if p.creator_id in creators
    ]


def add_manual(
    stores: Stores,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    data: PostCreate,
    tz: tzinfo,
) -> PostRead:
    """Add a post by link when sync missed it (e.g. the creator forgot the hashtag)."""
    campaign = _editable(stores, organisation_id, campaign_id)
    if data.posted_on > datetime.now(tz).date() + timedelta(days=1):
        raise InvalidRequest("The post date can't be in the future")

    handle, external_id = post_url_parts(data.url)
    creator = stores.creators.get_by_handle(organisation_id, Platform.TIKTOK, handle)
    if creator is None or stores.assignments.get(organisation_id, campaign_id, creator.id) is None:
        raise NotAssigned(handle, campaign.name)

    fields = {
        "campaign_id": campaign_id,
        "url": data.url,
        "posted_at": datetime.combine(data.posted_on, time.min, tz).astimezone(UTC),
        "caption": data.caption,
        "hashtags": extract_hashtags(data.caption),
        "views": data.views,
        "likes": data.likes,
        "comments": data.comments,
        "shares": data.shares,
        "match_source": MatchSource.MANUAL,
        "removed": False,
    }
    existing = stores.posts.get_by_external_id(
        organisation_id, creator.id, Platform.TIKTOK, external_id
    )
    if existing is None:
        new = Post(
            organisation_id=organisation_id,
            creator_id=creator.id,
            external_id=external_id,
            **fields,
        )
        post = stores.posts.add(new)
    elif existing.removed:
        # Removed earlier; bring it back. Sync will refresh its metrics if it sees it
        post = stores.posts.save(replace(existing, **fields))
    else:
        tracked_in = stores.campaigns.get(organisation_id, existing.campaign_id)
        raise AlreadyTracked(tracked_in.name if tracked_in else "another campaign")
    return to_read(post, creator)


def move(
    stores: Stores, organisation_id: uuid.UUID, post_id: uuid.UUID, data: PostMove
) -> PostRead:
    """Move a post that was matched to the wrong campaign. Sync won't move it back."""
    post = _get(stores, organisation_id, post_id)
    if data.campaign_id == post.campaign_id:
        return _read(stores, post)
    _editable(stores, organisation_id, post.campaign_id)
    destination = _editable(stores, organisation_id, data.campaign_id)
    creator = stores.creators.get(organisation_id, post.creator_id)
    if creator is None:
        raise PostNotFound
    if stores.assignments.get(organisation_id, destination.id, creator.id) is None:
        raise NotAssigned(creator.handle, destination.name)
    moved = stores.posts.save(
        replace(post, campaign_id=destination.id, match_source=MatchSource.MANUAL)
    )
    return to_read(moved, creator)


def remove(stores: Stores, organisation_id: uuid.UUID, post_id: uuid.UUID) -> None:
    """Stop counting a post. It's kept, flagged removed, so sync doesn't add it back."""
    post = _get(stores, organisation_id, post_id)
    _editable(stores, organisation_id, post.campaign_id)
    stores.posts.save(replace(post, removed=True, match_source=MatchSource.MANUAL))
