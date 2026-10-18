"""API settings, loaded from environment variables."""

from functools import cached_property
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://hookd:hookd@localhost:5432/hookd"
    redis_url: str = "redis://localhost:6379/0"
    aws_region: str = "ap-southeast-2"
    aws_endpoint_url: str | None = None  # local SQS only; never used for Cognito
    sync_queue_url: str = ""
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""

    # "inline" runs "Sync now" in the API process; "queue" sends it to the worker over
    # SQS. Inline until the API and worker share a database (the stores are in-memory).
    sync_mode: Literal["inline", "queue"] = "inline"
    sync_lookback_days: int = 30
    tiktok_mode: Literal["mock", "live"] = "mock"
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    # Campaign dates and target periods are calendar days in this timezone
    campaign_timezone: str = "Australia/Brisbane"

    @cached_property
    def campaign_tz(self) -> ZoneInfo:
        return ZoneInfo(self.campaign_timezone)


settings = Settings()
