"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.password import verify_password
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.service import (
    create_session,
    revoke_session,
)
from app.modules.users.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])

SESSION_COOKIE = "paym_session"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str


@router.post("/login", response_model=UserResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = data.email.strip().lower()

    user = db.scalar(select(User).where(User.email == email))

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token, csrf_token = create_session(db, user.id)
    db.commit()

    settings = get_settings()

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_absolute_seconds,
        path="/",
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
def current_user(
    user: User = Depends(get_current_user),
):
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    paym_session: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    if paym_session:
        revoke_session(db, paym_session)
        db.commit()

    response.delete_cookie(SESSION_COOKIE, path="/")
