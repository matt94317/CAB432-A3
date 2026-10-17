"""Mounts every route module under /api."""

from fastapi import APIRouter

from hookd_api.routes import (
    assignments,
    campaigns,
    creators,
    dashboard,
    health,
    me,
    posts,
    sync,
)

api_router = APIRouter()
for module in (health, me, campaigns, creators, assignments, posts, dashboard, sync):
    api_router.include_router(module.router)
