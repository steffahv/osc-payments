from fastapi.testclient import TestClient

from app.main import app


def test_rejects_missing_origin():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={})

    assert response.status_code == 403


def test_rejects_untrusted_origin():
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://untrusted.example"},
        json={},
    )

    assert response.status_code == 403


def test_allows_trusted_origin():
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:5173"},
        json={},
    )

    # Origin validation passes; login may reject invalid input.
    assert response.status_code != 403