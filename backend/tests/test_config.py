import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_preserves_special_password_characters():
    settings = Settings(_env_file=None, postgres_password="p@ss:/%?#word")
    assert settings.database_url.password == "p@ss:/%?#word"
    assert "p@ss:/%?#word" not in str(settings.database_url)


def test_production_requires_secure_cookies():
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(_env_file=None, app_env="production", cookie_secure=False, postgres_password="x" * 32)


def test_idle_timeout_cannot_exceed_absolute_timeout():
    with pytest.raises(ValidationError, match="Idle timeout"):
        Settings(_env_file=None, postgres_password="test", session_idle_seconds=100, session_absolute_seconds=50)
