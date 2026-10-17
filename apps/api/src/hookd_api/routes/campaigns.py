"""Campaign CRUD, archive and list with progress (US-03 to US-06)."""

from fastapi import APIRouter

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
