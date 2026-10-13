"""Typed configuration; never interpolate credentials into a URL manually."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WEB-PAYM"
    app_env: Literal["development", "test", "production"] = "development"
    postgres_user: str = "paym"
    postgres_password: SecretStr
    postgres_db: str = "paym"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = Field(default=55432, ge=1, le=65535)
    cookie_secure: bool = False
    session_absolute_seconds: int = Field(default=28800, gt=0)
    #time after which a session will be invalidated if there is no activity
    session_idle_seconds: int = Field(default=5400, gt=0)
    frontend_origin: str = "http://localhost:5173"

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.session_idle_seconds > self.session_absolute_seconds:
            raise ValueError("Idle timeout cannot exceed absolute session duration")
        if self.app_env == "production":
            if not self.cookie_secure:
                raise ValueError("Production requires COOKIE_SECURE=true")
            password = self.postgres_password.get_secret_value()
            if len(password) < 24 or password == "replace-with-generated-local-password":
                raise ValueError("Production requires a strong PostgreSQL password")
        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
