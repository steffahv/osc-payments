"""Master-data API tests with real PostgreSQL, sessions and RBAC; all data rolls back."""
import importlib.util
import os
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.modules.auth.service import create_session, utc_now
from app.modules.master_data.models import NodeType, UtilityType, Provider
from app.modules.permissions.models import Permission
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from app.modules.teams.models import Team, TeamMembership
from app.modules.users.models import User
from test_receipts import db as stage_two_db  # noqa: F401 -- isolated migration fixture

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]
path = Path(__file__).resolve().parents[1] / "alembic/versions/e4a109bc7283_initial_permission_catalog.py"
spec = importlib.util.spec_from_file_location(path.stem, path)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
BASE = "/api/v1/master-data"


@pytest.fixture
def db(stage_two_db):
    with Operations.context(MigrationContext.configure(stage_two_db.connection())):
        catalog.upgrade()
    yield stage_two_db


@pytest.fixture
def user(db):
    user = User(email="master-api@example.com", full_name="Test user", password_hash="test-only")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def client(db, user):
    app = create_app()
    connection = db.connection()

    def override_db():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as request_db:
            yield request_db

    app.dependency_overrides[get_db] = override_db
    token, _ = create_session(db, user.id)
    with TestClient(app, headers={"Origin": get_settings().frontend_origin}) as client:
        client.cookies.set("paym_session", token)
        yield client
    app.dependency_overrides.clear()


def grant(db, user, actions=("view", "manage"), scope="global"):
    role = Role(code="test_" + uuid4().hex, name="Reusable test role")
    db.add(role)
    db.flush()
    module_id = db.scalar(select(SystemModule.id).where(SystemModule.code == "master_data"))
    for action in actions:
        permission_id = db.scalar(select(Permission.id).where(
            Permission.module_id == module_id, Permission.action == action,
        ))
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))
    team_id = None
    if scope == "team":
        team = Team(code="team_" + uuid4().hex, name="Test team")
        db.add(team)
        db.flush()
        team_id = team.id
        db.add(TeamMembership(user_id=user.id, team_id=team_id))
        db.flush()
    assignment = UserRoleAssignment(user_id=user.id, role_id=role.id, scope=scope, team_id=team_id)
    db.add(assignment)
    db.flush()
    return role, assignment


READS = [(method, path) for method in ("GET",) for resource in (
    "utility-types", "node-types", "nodes", "providers", "service-accounts",
) for path in (resource, resource + "/" + str(uuid4()))]
WRITES = [(method, resource + ("/" + str(uuid4()) if method == "PATCH" else ""))
          for resource in ("nodes", "providers", "service-accounts") for method in ("POST", "PATCH")]


@pytest.mark.parametrize("method,path", READS + WRITES)
def test_every_endpoint_default_denies_and_excludes_team_grants(db, user, client, method, path):
    kwargs = {"json": {}} if method != "GET" else {}
    assert client.request(method, f"{BASE}/{path}", **kwargs).status_code == 403
    grant(db, user, scope="team")
    assert client.request(method, f"{BASE}/{path}", **kwargs).status_code == 403
    client.cookies.clear()
    assert client.request(method, f"{BASE}/{path}", **kwargs).status_code == 401


def test_catalog_seed_idempotent_preserves_existing_modules_and_grants(stage_two_db):
    db = stage_two_db
    module = SystemModule(code="admin", name="Existing administration", is_enabled=False)
    db.add(module)
    db.flush()
    existing_id = module.id
    with Operations.context(MigrationContext.configure(db.connection())):
        catalog.upgrade()
        catalog.upgrade()
    rows = db.execute(select(SystemModule.code, Permission.action).join(
        Permission, Permission.module_id == SystemModule.id,
    )).all()
    assert {f"{code}.{action}" for code, action in rows} == {
        "dashboard.view", "receipts.view", "receipts.create", "receipts.update",
        "reports.view", "reports.export", "master_data.view", "master_data.manage",
        "admin.users_manage", "admin.roles_manage",
    }
    assert len(rows) == 10
    db.refresh(module)
    assert module.id == existing_id and module.name == "Existing administration" and not module.is_enabled
    assert db.scalar(select(func.count()).select_from(SystemModule)) == 5
    assert db.scalar(select(func.count()).select_from(RolePermission)) == 0
    assert db.scalar(select(func.count()).select_from(UserRoleAssignment)) == 0


def test_full_crud_filters_and_preserved_identifiers(db, user, client):
    grant(db, user)
    node_type = str(db.scalar(select(NodeType.id).where(NodeType.code == "TX")))
    utility = str(db.scalar(select(UtilityType.id).where(UtilityType.code == "electricity")))
    resources = [
        ("providers", {"name": "Provider 100% literal", "tax_id": "00123", "region": "North"}),
        ("nodes", {"code": "T4249", "name": "T4249_SM_SANTA LUCIA", "node_type_id": node_type}),
    ]
    ids = {}
    for resource, data in resources:
        response = client.post(f"{BASE}/{resource}", json=data)
        assert response.status_code == 201, response.text
        ids[resource] = response.json()["id"]
    account = {
        "node_id": ids["nodes"], "provider_id": ids["providers"],
        "utility_type_id": utility, "supply_id": "001234567",
    }
    resources.append(("service-accounts", account))
    response = client.post(f"{BASE}/service-accounts", json=account)
    assert response.status_code == 201, response.text
    ids["service-accounts"] = response.json()["id"]
    assert response.json()["supply_id"] == "001234567"
    for field in ("node_id", "provider_id", "utility_type_id"):
        invalid = {**account, field: str(uuid4())}
        assert client.post(f"{BASE}/service-accounts", json=invalid).status_code == 422
        assert client.patch(f"{BASE}/service-accounts/{ids['service-accounts']}",
                            json={field: str(uuid4())}).status_code == 422
    for resource, data in resources:
        # Duplicate codes, tax IDs and supply IDs remain allowed.
        assert client.post(f"{BASE}/{resource}", json=data).status_code == 201
        path = f"{BASE}/{resource}/{ids[resource]}"
        assert client.get(path).status_code == 200
        for active in (False, True):
            response = client.patch(path, json={"is_active": active})
            assert response.status_code == 200 and response.json()["is_active"] is active
            page = client.get(f"{BASE}/{resource}", params={"is_active": str(active).lower()}).json()
            assert ids[resource] in {item["id"] for item in page["items"]}
        page = client.get(f"{BASE}/{resource}", params={"offset": 1, "limit": 1}).json()
        assert page["total"] == 2 and len(page["items"]) == 1 and page["offset"] == 1
        assert client.delete(path).status_code == 405
    response = client.patch(f"{BASE}/providers/{ids['providers']}", json={"tax_id": None, "region": None})
    assert response.status_code == 200 and response.json()["tax_id"] is None
    assert response.json()["name"] == "Provider 100% literal"
    assert client.get(f"{BASE}/providers", params={"q": "%"}).json()["total"] == 2
    assert client.get(f"{BASE}/providers", params={"q": "   "}).status_code == 200
    assert client.get(f"{BASE}/nodes", params={"node_type_id": str(uuid4())}).json()["total"] == 0
    for key in ("node_id", "provider_id", "utility_type_id"):
        assert client.get(f"{BASE}/service-accounts", params={key: account[key]}).json()["total"] == 2
        assert client.get(f"{BASE}/service-accounts", params={key: str(uuid4())}).json()["total"] == 0
    for resource in ("utility-types", "node-types"):
        response = client.get(f"{BASE}/{resource}")
        assert response.status_code == 200 and response.json()["total"] > 0
        record_id = response.json()["items"][0]["id"]
        assert client.get(f"{BASE}/{resource}/{record_id}").status_code == 200
        assert client.post(f"{BASE}/{resource}", json={}).status_code == 405
        assert client.patch(f"{BASE}/{resource}/{record_id}", json={"is_active": False}).status_code == 405


def test_view_and_manage_are_independent_additive_grants(db, user, client):
    grant(db, user, ("manage",))
    assert client.get(f"{BASE}/providers").status_code == 403
    assert client.post(f"{BASE}/providers", json={"name": "Test"}).status_code == 201
    grant(db, user, ("view",))
    assert client.get(f"{BASE}/providers").status_code == 200


def test_view_only_cannot_write(db, user, client):
    grant(db, user, ("view",))
    assert client.get(f"{BASE}/providers").status_code == 200
    assert client.post(f"{BASE}/providers", json={"name": "Test"}).status_code == 403


def test_seed_and_downgrade_preserve_existing_grants(db, user, client):
    grant(db, user, ("view",))
    before = db.scalar(select(func.count()).select_from(RolePermission))
    with Operations.context(MigrationContext.configure(db.connection())):
        catalog.upgrade()
        catalog.downgrade()
        catalog.upgrade()
    assert db.scalar(select(func.count()).select_from(RolePermission)) == before
    assert client.get(f"{BASE}/providers").status_code == 200


@pytest.mark.parametrize("change", ["role", "assignment", "permission", "module", "user"])
def test_access_changes_take_effect_next_request(db, user, client, change):
    role, assignment = grant(db, user)
    assert client.get(f"{BASE}/providers").status_code == 200
    if change == "role":
        role.is_active = False
    elif change == "assignment":
        assignment.revoked_at = utc_now()
    elif change == "permission":
        db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    elif change == "module":
        db.scalar(select(SystemModule).where(SystemModule.code == "master_data")).is_enabled = False
    else:
        user.is_active = False
    db.flush()
    assert client.get(f"{BASE}/providers").status_code == (401 if change == "user" else 403)


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"q": ""}, {"is_active": "invalid"}])
def test_invalid_pagination_and_filters(db, user, client, params):
    grant(db, user)
    assert client.get(f"{BASE}/providers", params=params).status_code == 422


@pytest.mark.parametrize("resource,payload", [
    ("providers", {"name": ""}), ("providers", {"name": "   "}),
    ("providers", {"name": "x" * 201}), ("providers", {"name": "Test", "unknown": 1}),
    ("nodes", {"code": "T4249", "name": "Test", "node_type_id": str(uuid4())}),
    ("service-accounts", {"node_id": str(uuid4()), "provider_id": str(uuid4()),
                          "utility_type_id": str(uuid4()), "supply_id": 123}),
])
def test_invalid_inputs(db, user, client, resource, payload):
    grant(db, user)
    assert client.post(f"{BASE}/{resource}", json=payload).status_code == 422


def test_patch_null_missing_records_and_origin_protection(db, user, client):
    grant(db, user)
    response = client.post(f"{BASE}/providers", json={"name": "Test"})
    path = f"{BASE}/providers/{response.json()['id']}"
    for payload in ({"name": None}, {"is_active": None}, {"unexpected": "value"}):
        assert client.patch(path, json=payload).status_code == 422
    assert client.get(f"{BASE}/providers/{uuid4()}").status_code == 404
    assert client.patch(f"{BASE}/providers/{uuid4()}", json={"name": "Test"}).status_code == 404
    assert client.get(f"{BASE}/providers/not-a-uuid").status_code == 422
    assert client.post(f"{BASE}/providers", json={"name": "Test"},
                       headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert db.scalar(select(func.count()).select_from(Provider)) == 1
