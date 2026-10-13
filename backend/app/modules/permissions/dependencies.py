"""Default-deny global permissions, queried on every request."""

import re
from collections.abc import Callable

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.permissions.models import Permission
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from app.modules.users.models import User


def require_permission(code: str) -> Callable[..., User]:
    """Use Depends(require_permission("module.action")); team grants are excluded."""
    if not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", code):
        raise ValueError("Permission must use module.action format")
    module, action = code.split(".")

    def check_permission(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        grant = (
            select(UserRoleAssignment.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .join(SystemModule, SystemModule.id == Permission.module_id)
            .where(
                UserRoleAssignment.user_id == user.id,
                UserRoleAssignment.scope == "global",
                UserRoleAssignment.team_id.is_(None),
                UserRoleAssignment.revoked_at.is_(None),
                Role.is_active.is_(True),
                SystemModule.is_enabled.is_(True),
                SystemModule.code == module,
                Permission.action == action,
            )
        )
        if not db.scalar(select(grant.exists())):
            raise HTTPException(status_code=403, detail="Permission denied")
        return user

    return check_permission
