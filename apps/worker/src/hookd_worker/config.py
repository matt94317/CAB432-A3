"""Worker settings, loaded from environment variables."""

from functools import cached_property
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    aws_region: str = "ap-southeast-2"
    aws_endpoint_url: str | None = None
    sync_queue_url: str = ""
    storage: Literal["dynamodb", "memory"] = "dynamodb"
    dynamodb_table: str = "hookd"
    dynamodb_endpoint_url: str | None = None  # DynamoDB Local; unset in AWS
    dynamodb_create_table: bool = False  # local only; Terraform creates it in AWS
    sync_lookback_days: int = 30
    tiktok_mode: Literal["mock", "live"] = "mock"
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    # Must match the API's: campaign dates are calendar days in this timezone
    campaign_timezone: str = "Australia/Brisbane"

    @cached_property
    def campaign_tz(self) -> ZoneInfo:
        return ZoneInfo(self.campaign_timezone)


settings = Settings()
