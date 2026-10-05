"""Typed settings from the environment (ARCHITECTURE.md > Repo layout > app/config.py).

Fails fast on missing/invalid values: importing this module raises SystemExit
with every bad field listed, instead of a bare traceback deep in some route.
"""
from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class FaultInjection(StrEnum):
    OFF = "off"
    TIMEOUT = "timeout"
    ERROR = "error"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_env: AppEnv = Field(alias="APP_ENV")
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    session_ttl_hours: int = Field(default=72, alias="SESSION_TTL_HOURS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Database ---
    database_url: str = Field(alias="DATABASE_URL")

    # --- LLM: OpenRouter ---
    llm_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_models_fast: str = Field(default="", alias="LLM_MODELS_FAST")
    llm_models_smart: str = Field(default="", alias="LLM_MODELS_SMART")
    llm_require_parameters: bool = Field(default=True, alias="LLM_REQUIRE_PARAMETERS")
    llm_app_name: str = Field(default="CareerPath", alias="LLM_APP_NAME")

    # --- LLM behavior ---
    llm_timeout_fast_s: int = Field(default=20, alias="LLM_TIMEOUT_FAST_S")
    llm_timeout_smart_s: int = Field(default=40, alias="LLM_TIMEOUT_SMART_S")
    llm_max_retries: int = Field(default=1, alias="LLM_MAX_RETRIES")
    llm_max_concurrency: int = Field(default=4, alias="LLM_MAX_CONCURRENCY")
    llm_daily_calls_per_user: int = Field(default=25, alias="LLM_DAILY_CALLS_PER_USER")
    llm_daily_budget_usd: float = Field(default=0.30, alias="LLM_DAILY_BUDGET_USD")
    llm_price_input_per_1m_usd: float = Field(default=0, alias="LLM_PRICE_INPUT_PER_1M_USD")
    llm_price_output_per_1m_usd: float = Field(default=0, alias="LLM_PRICE_OUTPUT_PER_1M_USD")

    # --- Agent and matching ---
    max_results: int = Field(default=5, alias="MAX_RESULTS")
    run_stale_after_s: int = Field(default=300, alias="RUN_STALE_AFTER_S")
    max_resume_revisions: int = Field(default=2, alias="MAX_RESUME_REVISIONS")

    # --- Ingestion ---
    ingest_source: str = Field(default="", alias="INGEST_SOURCE")
    ingest_max_listings: int = Field(default=500, alias="INGEST_MAX_LISTINGS")
    ingest_delay_s: int = Field(default=3, alias="INGEST_DELAY_S")
    ingest_user_agent: str = Field(default="CareerPathBot/0.1", alias="INGEST_USER_AGENT")

    # --- Security ---
    login_max_attempts_per_15m: int = Field(default=10, alias="LOGIN_MAX_ATTEMPTS_PER_15M")

    # --- Testing only ---
    fault_injection: FaultInjection = Field(default=FaultInjection.OFF, alias="FAULT_INJECTION")

    @field_validator("secret_key")
    @classmethod
    def secret_key_strong_enough(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters (.env.example asks for 32+ random bytes)")
        return v

    @field_validator("database_url")
    @classmethod
    def database_url_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("DATABASE_URL must be set")
        return v

    @field_validator("ingest_delay_s")
    @classmethod
    def ingest_delay_meets_scraping_rule(cls, v: int) -> int:
        if v < 3:
            raise ValueError("INGEST_DELAY_S must be >= 3 seconds (D-22, SR-11)")
        return v

    @model_validator(mode="after")
    def production_refuses_unsafe_config(self) -> Settings:
        if self.app_env == AppEnv.PRODUCTION:
            if self.fault_injection != FaultInjection.OFF:
                raise ValueError("FAULT_INJECTION must be 'off' when APP_ENV=production (SR-09)")
            if not self.llm_api_key:
                raise ValueError("LLM_API_KEY must be set when APP_ENV=production")
        return self

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_models_fast and self.llm_models_smart)


def _format_validation_error(exc: ValidationError) -> str:
    lines = ["Invalid configuration -- check your environment / .env file:"]
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"]) or "?"
        lines.append(f"  - {field}: {error['msg']}")
    return "\n".join(lines)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise SystemExit(_format_validation_error(exc)) from None
