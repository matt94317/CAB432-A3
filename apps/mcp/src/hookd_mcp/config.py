"""MCP server settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hookd_api_url: str = "http://localhost:8000/api"
    port: int = 8001  # PORT; 8080 on ECS


settings = Settings()
