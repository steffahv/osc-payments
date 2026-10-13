"""Integration tests for authentication sessions."""

import os
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_engine
from app.modules.auth.service import (
    create_session,
    get_valid_session,
    revoke_session,
    utc_now,
)
from app.modules.users.models import User


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DB_TESTS") != "1",
        reason="Set RUN_DB_TESTS=1 to run database tests",
    ),
]


def test_session_lifecycle():
    settings = get_settings()

    # The database must be disposable/test-only for this test.
    with get_engine().connect() as connection:
        transaction = connection.begin()

        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                user = User(
                    email=f"session-{uuid4().hex}@example.com",
                    full_name="Session Test User",
                    password_hash="test-only-placeholder",
                )
                db.add(user)
                db.flush()

                token, csrf_token = create_session(db, user.id)

                assert token
                assert csrf_token
                assert token != csrf_token

                auth_session = get_valid_session(db, token)
                assert auth_session is not None
                assert auth_session.user_id == user.id
                assert get_valid_session(db, "invalid-token") is None

                # Verify inactivity expiration.
                auth_session.created_at = utc_now() - timedelta(hours=9)
                auth_session.last_seen_at = utc_now()
                auth_session.expires_at = utc_now() - timedelta(hours=1)
                db.flush()

                assert get_valid_session(db, token) is None

                # Restore activity and verify absolute expiration.
                auth_session.last_seen_at = utc_now()
                auth_session.expires_at = utc_now() - timedelta(seconds=1)
                db.flush()

                assert get_valid_session(db, token) is None

                # Restore expiration and verify logout.
                auth_session.expires_at = utc_now() + timedelta(hours=1)
                db.flush()

                revoke_session(db, token)
                db.flush()

                assert get_valid_session(db, token) is None
        finally:
            transaction.rollback()