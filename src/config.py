"""Pydantic-settings based configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: str = Field("https://api.openai.com/v1", description="OpenAI base URL")
    openai_model: str = Field("gpt-4o-mini", description="Primary LLM model")

    # Orchestrator
    orchestrator_timeout_ms: int = Field(150, ge=50, le=5000)
    max_concurrent_agents: int = Field(5, ge=1, le=20)

    # Articulation Cortex
    articulation_temp_start: float = Field(1.2, ge=0.0, le=2.0)
    articulation_temp_end: float = Field(0.3, ge=0.0, le=2.0)
    articulation_max_tokens: int = Field(512, ge=1, le=4096)

    # Dialectic Council
    dialectic_max_tokens: int = Field(256, ge=1, le=1024)
    dialectic_stop_sequence: str = Field("|", description="Stop token for constrained generation")

    # Recency Buffer
    buffer_maxlen: int = Field(3, ge=1, le=10)
    compression_max_words: int = Field(50, ge=10, le=200)

    # Insight Spike
    insight_noise_std: float = Field(0.1, ge=0.0, le=1.0)
    insight_threshold: float = Field(0.3, ge=0.0, le=1.0)

    # Pruner Weights
    pruner_alpha: float = Field(0.5, ge=0.0, le=1.0)
    pruner_beta: float = Field(0.3, ge=0.0, le=1.0)
    pruner_gamma: float = Field(0.2, ge=0.0, le=1.0)
    pruner_top_k: int = Field(2, ge=1, le=5)

    # Logging
    log_level: str = Field("INFO")
    log_format: str = Field("json")


settings = Settings()
