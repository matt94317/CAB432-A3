"""Current user. First call after sign-up creates User + Organisation (US-01)."""

from fastapi import APIRouter

router = APIRouter(prefix="/me", tags=["me"])
