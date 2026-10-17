"""Campaign dashboard: posts vs target, totals, behind-target creators (US-19, US-20, US-22)."""

from fastapi import APIRouter

router = APIRouter(prefix="/campaigns/{campaign_id}/dashboard", tags=["dashboard"])
