"""Receipt API tests with real PostgreSQL sessions/RBAC and rollback isolation."""
import os
from decimal import Decimal
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from app.modules.master_data.models import ServiceAccount, UtilityType
from app.modules.permissions.models import Permission
from app.modules.receipts.models import Receipt, ElectricityReceiptDetails, ReceiptWorkflowEvent
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from app.modules.teams.models import Team, TeamMembership
from test_receipts import account, db as stage_two_db  # noqa: F401
from test_receipt_history import migration as history_migration
from test_master_data_api import db as catalog_db, user, client  # noqa: F401

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]
BASE = "/api/v1/receipts"


@pytest.fixture
def db(catalog_db):
    with Operations.context(MigrationContext.configure(catalog_db.connection())):
        history_migration.upgrade()
    yield catalog_db


def grant(db, user, actions=("view", "create", "update"), scope="global"):
    role = Role(code="receipt_test_" + uuid4().hex, name="Receipt test role")
    db.add(role)
    db.flush()
    module_id = db.scalar(select(SystemModule.id).where(SystemModule.code == "receipts"))
    for action in actions:
        permission_id = db.scalar(select(Permission.id).where(
            Permission.module_id == module_id, Permission.action == action,
        ))
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))
    team_id = None
    if scope == "team":
        team = Team(code="test_" + uuid4().hex, name="Test team")
        db.add(team)
        db.flush()
        team_id = team.id
        db.add(TeamMembership(user_id=user.id, team_id=team.id))
        db.flush()
    assignment = UserRoleAssignment(user_id=user.id, role_id=role.id, scope=scope, team_id=team_id)
    db.add(assignment)
    db.flush()
    return assignment


@pytest.mark.parametrize("method,suffix", [("GET", ""), ("GET", "/id"), ("POST", ""), ("PATCH", "/id")])
def test_default_deny_and_team_grants(db, user, client, account, method, suffix):
    path = BASE + suffix.replace("id", str(uuid4()))
    kwargs = {"json": {"service_account_id": str(account.id)}} if method in ("POST", "PATCH") else {}
    assert client.request(method, path, **kwargs).status_code == 403
    grant(db, user, scope="team")
    assert client.request(method, path, **kwargs).status_code == 403
    client.cookies.clear()
    assert client.request(method, path, **kwargs).status_code == 401


def test_drafts_attribution_defaults_and_decimal_crud(db, user, client, account):
    grant(db, user)
    response = client.post(BASE, json={"service_account_id": str(account.id)})
    assert response.status_code == 201, response.text
    draft = response.json()
    assert draft["status"] == "draft" and draft["status_crm"] == "pending" and draft["currency_code"] == "PEN"
    assert draft["created_by"] == str(user.id)
    assert draft["amount"] is None and draft["electricity_details"] is None
    path = f"{BASE}/{draft['id']}"
    payload = {"receipt_number": "R-001", "amount": "1234567890123456.78",
               "period_start": "2026-10-01", "period_end": "2026-10-31",
               "electricity_details": {"consumption_kwh": "12345678901.234"}}
    response = client.patch(path, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["amount"] == "1234567890123456.78"
    assert response.json()["electricity_details"]["consumption_kwh"] == "12345678901.234"
    response = client.patch(path, json={"receipt_number": None, "electricity_details": {}})
    assert response.status_code == 200 and response.json()["receipt_number"] is None
    assert response.json()["electricity_details"]["consumption_kwh"] == "12345678901.234"
    response = client.patch(path, json={"amount": None, "electricity_details": {"consumption_kwh": None}})
    assert response.status_code == 200 and response.json()["amount"] is None
    assert response.json()["electricity_details"]["consumption_kwh"] is None
    assert client.get(path).json()["created_by"] == str(user.id)
    assert client.delete(path).status_code == 405
    assert db.scalar(select(func.count()).select_from(ReceiptWorkflowEvent)) == 0


@pytest.mark.parametrize("field,value", [
    ("status", "paid"), ("status_crm", "registered"), ("created_by", str(uuid4())),
    ("amount", "1.234"), ("amount", "10000000000000000"), ("amount", "NaN"),
    ("currency_code", None), ("currency_code", "PE"), ("service_account_id", None),
    ("service_account_id", str(uuid4())), ("receipt_number", "x" * 101),
    ("electricity_details", None), ("electricity_details", {"consumption_kwh": "1.2345"}),
    ("electricity_details", {"consumption_kwh": "100000000000"}),
    ("electricity_details", {"unknown": 1}),
])
def test_invalid_and_read_only_inputs_on_post_and_patch(db, user, client, account, field, value):
    grant(db, user)
    receipt = Receipt(service_account_id=account.id)
    db.add(receipt)
    db.flush()
    response = client.post(BASE, json={"service_account_id": str(account.id), field: value})
    assert response.status_code == 422, response.text
    assert client.patch(f"{BASE}/{receipt.id}", json={field: value}).status_code == 422


def test_merged_period_dates_and_nullable_drafts(db, user, client, account):
    grant(db, user)
    response = client.post(BASE, json={"service_account_id": str(account.id),
        "period_start": "2026-10-01", "period_end": "2026-10-31"})
    path = f"{BASE}/{response.json()['id']}"
    assert client.patch(path, json={"period_start": "2026-11-01"}).status_code == 422
    assert client.patch(path, json={"period_end": "2026-09-30"}).status_code == 422
    assert client.get(path).json()["period_start"] == "2026-10-01"
    assert client.patch(path, json={"period_end": None, "period_start": "2026-11-01"}).status_code == 200
    assert client.post(BASE, json={"service_account_id": str(account.id),
        "period_start": "2026-10-31", "period_end": "2026-10-01"}).status_code == 422


def test_electricity_utility_validation_and_account_changes(db, user, client, account):
    grant(db, user)
    other = UtilityType(code="test_other", name="Fixture only")
    db.add(other)
    db.flush()
    other_account = ServiceAccount(node_id=account.node_id, provider_id=account.provider_id,
                                   utility_type_id=other.id, supply_id="test")
    db.add(other_account)
    db.flush()
    assert client.post(BASE, json={"service_account_id": str(other_account.id),
                                  "electricity_details": {}}).status_code == 422
    response = client.post(BASE, json={"service_account_id": str(account.id), "electricity_details": {}})
    path = f"{BASE}/{response.json()['id']}"
    assert client.patch(path, json={"service_account_id": str(other_account.id)}).status_code == 422
    assert client.get(path).json()["service_account_id"] == str(account.id)


def test_permissions_are_independent_and_revocation_is_immediate(db, user, client, account):
    grant(db, user, ("create",))
    response = client.post(BASE, json={"service_account_id": str(account.id)})
    assert response.status_code == 201
    path = f"{BASE}/{response.json()['id']}"
    assert client.get(BASE).status_code == 403 and client.get(path).status_code == 403
    assert client.patch(path, json={}).status_code == 403
    view_assignment = grant(db, user, ("view",))
    assert client.get(path).status_code == 200
    assert client.patch(path, json={}).status_code == 403
    grant(db, user, ("update",))
    assert client.patch(path, json={"amount": "1.25"}).status_code == 200
    from app.modules.auth.service import utc_now
    view_assignment.revoked_at = utc_now()
    db.flush()
    assert client.get(path).status_code == 403


def test_list_filters_pagination_and_duplicates(db, user, client, account):
    grant(db, user)
    for _ in range(3):
        assert client.post(BASE, json={"service_account_id": str(account.id),
                                      "receipt_number": "R%001", "electricity_details": {
                                          "consumption_kwh": "1.234"}}).status_code == 201
    response = client.get(BASE, params={"offset": 1, "limit": 1, "status": "draft",
        "status_crm": "pending", "service_account_id": str(account.id), "q": "%"}).json()
    assert response["total"] == 3 and len(response["items"]) == 1
    assert response["items"][0]["electricity_details"]["consumption_kwh"] == "1.234"
    assert client.get(BASE, params={"status": "paid"}).json()["total"] == 0
    assert client.get(BASE, params={"status_crm": "registered"}).json()["total"] == 0
    assert client.get(BASE, params={"service_account_id": str(uuid4())}).json()["total"] == 0
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"q": ""}):
        assert client.get(BASE, params=params).status_code == 422
    assert client.get(f"{BASE}/{uuid4()}").status_code == 404
    assert client.patch(f"{BASE}/{uuid4()}", json={}).status_code == 404
    assert client.get(f"{BASE}/invalid").status_code == 422
    assert client.post(BASE, json={"service_account_id": str(account.id)},
                       headers={"Origin": "https://untrusted.example"}).status_code == 403


@pytest.mark.parametrize("method", ["POST", "PATCH"])
def test_receipt_and_details_rollback_together(db, user, client, account, method):
    grant(db, user)
    path = BASE
    if method == "PATCH":
        existing = client.post(BASE, json={"service_account_id": str(account.id), "amount": "10.00",
            "electricity_details": {"consumption_kwh": "5.000"}}).json()
        path += "/" + existing["id"]
    before = db.scalar(select(func.count()).select_from(Receipt))
    connection = db.connection()

    def fail_detail_write(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(("INSERT INTO ELECTRICITY_RECEIPT_DETAILS",
                                                 "UPDATE ELECTRICITY_RECEIPT_DETAILS")):
            raise IntegrityError("forced detail failure", {}, Exception("test failure"))

    event.listen(connection, "before_cursor_execute", fail_detail_write)
    try:
        response = client.request(method, path, json={"service_account_id": str(account.id),
            "amount": "20.00", "electricity_details": {"consumption_kwh": "7.000"}})
        assert response.status_code == 409
        assert response.json() == {"detail": "Operation conflicts with related data"}
    finally:
        event.remove(connection, "before_cursor_execute", fail_detail_write)
    assert db.scalar(select(func.count()).select_from(Receipt)) == before
    if method == "PATCH":
        saved = client.get(path).json()
        assert Decimal(saved["amount"]) == Decimal("10")
        assert Decimal(saved["electricity_details"]["consumption_kwh"]) == Decimal("5")
    else:
        assert db.scalar(select(func.count()).select_from(ElectricityReceiptDetails)) == 0
