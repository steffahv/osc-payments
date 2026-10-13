"""Reusable authentication using the existing PostgreSQL session lifecycle."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.service import get_valid_session
from app.modules.users.models import User


def get_current_user(
    paym_session: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
) -> User:
    if not paym_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_valid_session(db, paym_session)
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if db.is_modified(session):
        db.commit()
    return user
