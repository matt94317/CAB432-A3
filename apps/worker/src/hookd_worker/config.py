"""Worker settings, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://hookd:hookd@localhost:5432/hookd"
    redis_url: str = "redis://localhost:6379/0"
    aws_region: str = "ap-southeast-2"
    aws_endpoint_url: str | None = None
    sync_queue_url: str = ""
    tiktok_mode: str = "mock"  # "mock" or "live"
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""


settings = Settings()
