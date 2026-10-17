"""Manual post entry, move or remove posts (US-15, US-16)."""

from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["posts"])
