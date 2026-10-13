"""Minimal server-side authentication session management."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.session_security import generate_session_token, hash_token
from app.modules.auth.models import AuthSession


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(db: Session, user_id: UUID) -> tuple[str, str]:
    """Create a session and return its raw session and CSRF tokens."""
    settings = get_settings()
    now = utc_now()

    session_token = generate_session_token()
    csrf_token = generate_session_token()

    auth_session = AuthSession(
        user_id=user_id,
        token_hash=hash_token(session_token),
        csrf_token_hash=hash_token(csrf_token),
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(
            seconds=settings.session_absolute_seconds
        ),
    )

    db.add(auth_session)
    db.flush()

    return session_token, csrf_token


def get_valid_session(db: Session, token: str) -> AuthSession | None:
    """Return a session only when active and not expired."""
    settings = get_settings()
    now = utc_now()

    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(token)
        )
    )

    if auth_session is None or auth_session.revoked_at is not None:
        return None

    if now >= auth_session.expires_at:
        return None

    idle_seconds = (now - auth_session.last_seen_at).total_seconds()

    if idle_seconds >= settings.session_idle_seconds:
        return None

    # Reduce unnecessary database writes.
    if idle_seconds >= 60:
        auth_session.last_seen_at = now

    return auth_session


def revoke_session(db: Session, token: str) -> None:
    """Revoke an existing session."""
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(token)
        )
    )

    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = utc_now()