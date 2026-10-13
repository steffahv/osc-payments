
"""Integration test for login, current user, and logout."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.password import hash_password
from app.db.session import get_db, get_engine
from app.main import app
from app.modules.users.models import User


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DB_TESTS") != "1",
        reason="Set RUN_DB_TESTS=1 to run database tests",
    ),
]


def test_authentication_flow():
    password = "TestPassword123!"
    email = f"auth-{uuid4().hex}@example.com"

    with get_engine().connect() as connection:
        transaction = connection.begin()

        def override_get_db():
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                user = User(
                    email=email,
                    full_name="Authentication Test User",
                    password_hash=hash_password(password),
                )
                db.add(user)
                db.commit()
                user_id = str(user.id)

            with TestClient(app) as client:
                origin = {"Origin": "http://localhost:5173"}

                # Unauthenticated access.
                assert client.get("/api/v1/auth/me").status_code == 401

                # Incorrect password.
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": "WrongPassword"},
                    headers=origin,
                )
                assert response.status_code == 401

                # Successful login.
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                    headers=origin,
                )
                assert response.status_code == 200
                assert response.json()["id"] == user_id
                assert client.cookies.get("paym_session")

                # Authenticated request.
                response = client.get("/api/v1/auth/me")
                assert response.status_code == 200
                assert response.json()["email"] == email

                # Logout.
                response = client.post(
                    "/api/v1/auth/logout",
                    headers=origin,
                )
                assert response.status_code == 204

                # Session must no longer work.
                assert client.get("/api/v1/auth/me").status_code == 401

        finally:
            app.dependency_overrides.pop(get_db, None)
            transaction.rollback()
