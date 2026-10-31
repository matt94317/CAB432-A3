"""MCP server settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hookd_api_url: str = "http://localhost:8000/api"
    port: int = 8001  # PORT; 8080 on ECS

    # In-app assistant: chat model provider (see llm.py)
    llm_provider: Literal["bedrock", "openrouter"] = "bedrock"
    aws_region: str = "ap-southeast-2"
    bedrock_model_id: str = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-haiku-5.5"
    chat_max_steps: int = 6  # model calls per message, so a confused loop can't run up cost
    chat_max_tokens: int = 1024
    campaign_timezone: str = "Australia/Brisbane"


settings = Settings()
