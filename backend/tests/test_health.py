import asyncio
from unittest.mock import Mock

from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import create_app


def request(app, path):
    # ASGITransport avoids the deprecated Starlette httpx adapter.
    # These tests do not open real engines or require a PostgreSQL lifespan.
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(path)
    return asyncio.run(run())


def test_liveness_does_not_require_database():
    response = request(create_app(), "/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database():
    app = create_app()
    db = Mock()
    app.dependency_overrides[get_db] = lambda: db
    response = request(app, "/api/v1/health/ready")
    assert response.status_code == 200
    db.execute.assert_called_once()


def test_readiness_failure_does_not_leak_connection_details():
    app = create_app()
    db = Mock()
    db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("secret-server-password"))
    app.dependency_overrides[get_db] = lambda: db
    response = request(app, "/api/v1/health/ready")
    assert response.status_code == 503
    assert "secret-server-password" not in response.text
    assert response.json()["detail"] == "Service temporarily unavailable"
