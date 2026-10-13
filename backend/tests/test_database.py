"""Optional integration test against the Compose PostgreSQL database."""

import os

import pytest
from sqlalchemy import text

from app.db.session import get_engine


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1 with PostgreSQL available")
def test_postgresql_connection():
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert "PostgreSQL" in connection.execute(text("SELECT version()")).scalar_one()
