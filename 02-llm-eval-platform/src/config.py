from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    log_level: str = "INFO"
    results_table: str = "AGENTICOPS-eval-results"
    dataset_bucket: str = "AGENTICOPS-eval-datasets"
    tracing_enabled: bool = True

    class Config:
        env_prefix = "AGENTICOPS_"


settings = Settings()
