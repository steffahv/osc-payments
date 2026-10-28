"""Explicit development-only grants; previews unless --apply is supplied."""
import argparse
import json
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models  # noqa: F401 -- register FK metadata for standalone use
from app.db.session import get_engine
from app.modules.permissions.models import Permission
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from app.modules.users.models import User


def assign_permissions(db: Session, email: str, role_code: str, codes: list[str], *, apply: bool = False):
    if get_settings().app_env != "development":
        raise ValueError("This command is available only in development")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", role_code):
        raise ValueError("Invalid role code")
    if not codes:
        raise ValueError("Specify at least one permission")
    user = db.scalar(select(User).where(User.email == email.strip().lower()).with_for_update())
    if user is None or not user.is_active:
        raise ValueError("An existing active user is required")
    permission_ids = set()
    for code in set(codes):
        if not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", code):
            raise ValueError("Permission must use module.action format")
        module, action = code.split(".")
        permission_id = db.scalar(select(Permission.id).join(
            SystemModule, SystemModule.id == Permission.module_id,
        ).where(SystemModule.code == module, SystemModule.is_enabled.is_(True),
                Permission.action == action))
        if permission_id is None:
            raise ValueError(f"Permission is missing or its module is disabled: {code}")
        permission_ids.add(permission_id)
    role = db.scalar(select(Role).where(Role.code == role_code).with_for_update())
    if role is not None:
        existing = set(db.scalars(select(RolePermission.permission_id).where(RolePermission.role_id == role.id)))
        if not role.is_active or existing != permission_ids:
            raise ValueError("Existing role must be active and have exactly the requested permissions; choose a new role code")
    plan = {"email": user.email, "role": role_code, "permissions": sorted(set(codes)),
            "scope": "global", "applied": apply}
    if not apply:
        return plan
    if role is None:
        role = Role(code=role_code, name=f"Development access: {role_code}")
        db.add(role)
        db.flush()
        db.add_all([RolePermission(role_id=role.id, permission_id=permission_id)
                    for permission_id in permission_ids])
    assignment = db.scalar(select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id, UserRoleAssignment.role_id == role.id,
        UserRoleAssignment.scope == "global", UserRoleAssignment.team_id.is_(None),
        UserRoleAssignment.revoked_at.is_(None),
    ))
    if assignment is None:
        db.add(UserRoleAssignment(user_id=user.id, role_id=role.id, scope="global"))
    db.flush()
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role-code", required=True)
    parser.add_argument("--permission", action="append", required=True)
    parser.add_argument("--apply", action="store_true", help="Persist the explicit grant; otherwise preview only")
    args = parser.parse_args()
    if get_settings().app_env != "development":
        parser.error("This command is available only in development")
    try:
        with Session(get_engine()) as db:
            plan = assign_permissions(db, args.email, args.role_code, args.permission, apply=args.apply)
            if args.apply:
                db.commit()
            else:
                db.rollback()
    except ValueError as exc:
        parser.error(str(exc))
    except IntegrityError:
        parser.error("Concurrent grant conflict; no changes saved. Retry after reviewing the role.")
    print(json.dumps(plan))


if __name__ == "__main__":
    main()
