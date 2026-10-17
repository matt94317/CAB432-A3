"""MCP server settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hookd_api_url: str = "http://localhost:8000/api"


settings = Settings()
