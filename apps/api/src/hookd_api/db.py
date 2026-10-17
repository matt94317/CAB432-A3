"""Database engine and session factory for the API process."""

from hookd_api.config import settings
from hookd_core.db import make_engine, make_session_factory

engine = make_engine(settings.database_url)
SessionLocal = make_session_factory(engine)
