"""Trigger a manual sync and report last-synced time (US-13, US-18)."""

from fastapi import APIRouter

router = APIRouter(prefix="/sync", tags=["sync"])
