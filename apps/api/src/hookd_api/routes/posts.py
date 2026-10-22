"""A campaign's posts, manual post entry, move or remove posts (US-15 to US-17).

Every route is scoped to the signed-in user's organisation.
"""

import uuid

from fastapi import APIRouter, Response, status

from hookd_api.deps import AllStores, CampaignTz, CurrentUser
from hookd_api.schemas.post import PostCreate, PostMove, PostRead
from hookd_api.services import posts as service

router = APIRouter(tags=["posts"])

NOT_FOUND = {404: {"description": "Campaign or post not found in your organisation"}}
ARCHIVED = {409: {"description": "Campaign is archived"}}
NOT_ASSIGNED = {422: {"description": "The post's creator isn't assigned to the campaign"}}


@router.get("/posts", response_model=list[PostRead])
def list_posts(user: CurrentUser, stores: AllStores) -> list[PostRead]:
    """Every tracked post across your campaigns, newest first."""
    return service.list_all(stores, user.organisation_id)


@router.get("/campaigns/{campaign_id}/posts", response_model=list[PostRead], responses=NOT_FOUND)
def list_campaign_posts(
    campaign_id: uuid.UUID, user: CurrentUser, stores: AllStores
) -> list[PostRead]:
    """Posts counting toward this campaign, newest first, with their latest metrics."""
    return service.list_for_campaign(stores, user.organisation_id, campaign_id)


@router.post(
    "/campaigns/{campaign_id}/posts",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        **NOT_FOUND,
        409: {"description": "Campaign is archived, or the post is already tracked"},
        **NOT_ASSIGNED,
    },
)
def add_post(
    campaign_id: uuid.UUID, data: PostCreate, user: CurrentUser, stores: AllStores, tz: CampaignTz
) -> PostRead:
    """Add a post by link when sync missed it. Sync won't move or remove it."""
    return service.add_manual(stores, user.organisation_id, campaign_id, data, tz)


@router.patch(
    "/posts/{post_id}", response_model=PostRead, responses={**NOT_FOUND, **ARCHIVED, **NOT_ASSIGNED}
)
def move_post(post_id: uuid.UUID, data: PostMove, user: CurrentUser, stores: AllStores) -> PostRead:
    """Move a post to another campaign its creator is on."""
    return service.move(stores, user.organisation_id, post_id, data)


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **ARCHIVED},
)
def remove_post(post_id: uuid.UUID, user: CurrentUser, stores: AllStores) -> Response:
    """Stop counting a post toward its campaign. Sync won't add it back."""
    service.remove(stores, user.organisation_id, post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
