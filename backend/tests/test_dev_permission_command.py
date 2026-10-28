"""Development grants require explicit application and never alter shared roles."""
import os
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.cli import grant_dev_permissions as command
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from test_receipts import db as stage_two_db  # noqa: F401
from test_master_data_api import db, user  # noqa: F401

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]
CODES = ["receipts.view", "receipts.create", "receipts.update"]


@pytest.fixture(autouse=True)
def development(monkeypatch):
    monkeypatch.setattr(command, "get_settings", lambda: SimpleNamespace(app_env="development"))


def test_preview_does_not_grant_and_apply_is_idempotent(db, user):
    plan = command.assign_permissions(db, user.email, "dev_receipts", CODES)
    assert plan["applied"] is False and plan["permissions"] == sorted(CODES)
    assert db.scalar(select(func.count()).select_from(Role)) == 0
    assert db.scalar(select(func.count()).select_from(UserRoleAssignment)) == 0
    for _ in range(2):
        assert command.assign_permissions(db, user.email, "dev_receipts", CODES, apply=True)["applied"]
    assert db.scalar(select(func.count()).select_from(Role)) == 1
    assert db.scalar(select(func.count()).select_from(RolePermission)) == 3
    assignment = db.scalar(select(UserRoleAssignment))
    assert assignment.user_id == user.id and assignment.scope == "global" and assignment.team_id is None
    assert db.scalar(select(func.count()).select_from(UserRoleAssignment)) == 1


@pytest.mark.parametrize("environment", ["production", "test"])
def test_non_development_refused(db, user, monkeypatch, environment):
    monkeypatch.setattr(command, "get_settings", lambda: SimpleNamespace(app_env=environment))
    with pytest.raises(ValueError, match="only in development"):
        command.assign_permissions(db, user.email, "dev_receipts", CODES, apply=True)
    assert db.scalar(select(func.count()).select_from(Role)) == 0


@pytest.mark.parametrize("case", ["unknown_user", "inactive_user", "unknown_permission", "disabled_module",
                                  "invalid_role", "no_permissions", "invalid_permission"])
def test_invalid_grants_make_no_changes(db, user, case):
    email, role, codes = user.email, "dev_receipts", CODES
    if case == "unknown_user":
        email = "missing@example.com"
    elif case == "inactive_user":
        user.is_active = False
    elif case == "unknown_permission":
        codes = ["receipts.missing"]
    elif case == "disabled_module":
        db.scalar(select(SystemModule).where(SystemModule.code == "receipts")).is_enabled = False
    elif case == "invalid_role":
        role = "invalid.role"
    elif case == "no_permissions":
        codes = []
    else:
        codes = ["admin.users.manage"]
    db.flush()
    with pytest.raises(ValueError):
        command.assign_permissions(db, email, role, codes, apply=True)
    assert db.scalar(select(func.count()).select_from(Role)) == 0
    assert db.scalar(select(func.count()).select_from(UserRoleAssignment)) == 0


def test_existing_role_cannot_be_silently_expanded_or_reactivated(db, user):
    command.assign_permissions(db, user.email, "dev_receipts", ["receipts.view"], apply=True)
    with pytest.raises(ValueError, match="exactly"):
        command.assign_permissions(db, user.email, "dev_receipts", CODES, apply=True)
    role = db.scalar(select(Role))
    role.is_active = False
    db.flush()
    with pytest.raises(ValueError, match="active"):
        command.assign_permissions(db, user.email, "dev_receipts", ["receipts.view"], apply=True)
    assert db.scalar(select(func.count()).select_from(RolePermission)) == 1
