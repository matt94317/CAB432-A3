"""Assign creators to campaigns, set/change targets, unassign (US-09 to US-12)."""

from fastapi import APIRouter

router = APIRouter(prefix="/campaigns/{campaign_id}/creators", tags=["assignments"])
