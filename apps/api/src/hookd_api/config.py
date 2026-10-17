"""API settings, loaded from environment variables."""

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


settings = Settings()
