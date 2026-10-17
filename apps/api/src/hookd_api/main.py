"""FastAPI app entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from hookd_api.errors import DomainError
from hookd_api.routes import api_router

app = FastAPI(title="Hookd Tracker API")
app.include_router(api_router, prefix="/api")


@app.exception_handler(DomainError)
def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
