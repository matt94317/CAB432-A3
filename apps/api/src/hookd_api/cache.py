"""Dashboard cache for the API process, and the middleware that invalidates it.

Any successful write request (POST, PATCH, PUT, DELETE) invalidates the signed-in
organisation's dashboards. That covers every change made through the API,
including "Sync now"; the worker invalidates after its own syncs.
"""

from collections.abc import Awaitable, Callable
from functools import lru_cache

from fastapi import FastAPI, Request, Response

from hookd_api.config import settings
from hookd_core.cache import DashboardCache, make_cache

WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


@lru_cache
def get_cache() -> DashboardCache:
    return make_cache(settings.redis_url, settings.dashboard_cache_ttl_seconds)


def install_invalidation(app: FastAPI) -> None:
    @app.middleware("http")
    async def invalidate_on_write(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        organisation_id = getattr(request.state, "organisation_id", None)
        if request.method in WRITE_METHODS and response.status_code < 400 and organisation_id:
            cache = app.dependency_overrides.get(get_cache, get_cache)()
            cache.invalidate(organisation_id)
        return response
