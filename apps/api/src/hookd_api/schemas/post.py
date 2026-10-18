"""Post request and response models: manual entry, move, list (US-15 to US-18)."""

import re
import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from hookd_core.enums import MatchSource, Platform

# https://www.tiktok.com/@handle/video/7350000000000000000 (also m.tiktok.com, /photo/)
_POST_URL = re.compile(
    r"^(?:https?://)?(?:www\.|m\.)?tiktok\.com/@([a-z0-9_.]{2,24})/(video|photo)/(\d{5,25})"
    r"(?:[/?#].*)?$",
    re.IGNORECASE,
)
_SHORT_LINK = re.compile(r"^(?:https?://)?(?:vm|vt)\.tiktok\.com/|tiktok\.com/t/", re.IGNORECASE)


def canonical_post_url(raw: str) -> str:
    """Any full TikTok post link -> 'https://www.tiktok.com/@handle/video/<id>'."""
    url = raw.strip()
    if _SHORT_LINK.search(url):
        raise ValueError(
            "Short links can't be read. Open it, then copy the full link "
            "(tiktok.com/@handle/video/…)"
        )
    match = _POST_URL.match(url)
    if not match:
        raise ValueError("Paste a TikTok post link like tiktok.com/@handle/video/1234…")
    handle, kind, post_id = match.groups()
    return f"https://www.tiktok.com/@{handle.lower()}/{kind.lower()}/{post_id}"


def post_url_parts(canonical_url: str) -> tuple[str, str]:
    """(handle, post id) from a URL that has been through canonical_post_url."""
    handle, _, post_id = _POST_URL.match(canonical_url).groups()  # type: ignore[union-attr]
    return handle, post_id


Count = Annotated[int, Field(ge=0, le=10**12)]


class PostCreate(BaseModel):
    """A post the sync missed. The creator is found from the @handle in the link."""

    url: Annotated[str, Field(max_length=500), AfterValidator(canonical_post_url)]
    posted_on: date = Field(description="Day it was posted, in the campaign timezone")
    caption: str = Field(default="", max_length=2200, description="Hashtags are read from it")
    views: Count = 0
    likes: Count = 0
    comments: Count = 0
    shares: Count = 0


class PostMove(BaseModel):
    campaign_id: uuid.UUID = Field(description="Campaign the post should count toward")


class PostCreator(BaseModel):
    id: uuid.UUID
    name: str
    handle: str


class PostRead(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    creator: PostCreator
    platform: Platform
    url: str
    caption: str
    hashtags: list[str]
    posted_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    match_source: MatchSource = Field(description="hashtag: matched by sync; manual: set by you")
    last_synced_at: datetime | None = Field(description="Null until sync has seen this post")
    created_at: datetime
    updated_at: datetime
