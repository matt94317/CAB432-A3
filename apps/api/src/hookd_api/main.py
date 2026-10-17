"""FastAPI app entry point."""

from fastapi import FastAPI

from hookd_api.routes import api_router

app = FastAPI(title="Hookd Tracker API")
app.include_router(api_router, prefix="/api")
