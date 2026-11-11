"""Global configuration and thresholds for the triage agent."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "fde-agentic-order-triage"
    environment: str = "production"
    log_level: str = "INFO"

    # Model configuration
    model_name: str = "gpt-4o"
    openai_api_key: str = "sk-placeholder-enterprise"
    temperature: float = 0.0

    # Business invariants & Guardrails
    high_value_threshold_usd: float = 25000.0
    confidence_threshold: float = 0.85
    databricks_catalog: str = "enterprise_ai"
    databricks_schema: str = "order_intelligence"

    # Observability & Langfuse
    langfuse_public_key: str = "pk-lf-placeholder"
    langfuse_secret_key: str = "sk-lf-placeholder"
    langfuse_host: str = "https://cloud.langfuse.com"
    enable_langfuse: bool = True

    # Prometheus Metrics
    prometheus_metrics_port: int = 9090

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
