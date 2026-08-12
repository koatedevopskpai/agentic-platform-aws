from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    session_table: str = "AGENTICOPS-sessions-01"
    artifact_bucket: str = "AGENTICOPS-artifacts-01"
    log_level: str = "INFO"
    graph_timeout_seconds: int = 60
    worker_timeout_seconds: int = 30
    max_reflection_retries: int = 2

    class Config:
        env_prefix = "AGENTICOPS_"


settings = Settings()
