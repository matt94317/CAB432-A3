"""Creator roster CRUD (US-07, US-08) and creator performance view (US-21)."""

from fastapi import APIRouter

router = APIRouter(prefix="/creators", tags=["creators"])
