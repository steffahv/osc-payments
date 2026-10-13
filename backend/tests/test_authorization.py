"""Integration tests for default-deny global RBAC."""

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.password import hash_password
from app.db.session import get_db, get_engine
from app.modules.auth.service import create_session
from app.modules.permissions.dependencies import require_permission
from app.modules.permissions.models import Permission
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.system_modules.models import SystemModule
from app.modules.users.models import User
from app.modules.teams.models import Team,TeamMembership


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 to run database tests",
)


def test_global_permission_enforcement():
    app = FastAPI()

    @app.get("/protected")
    def protected(user: User = Depends(require_permission("payments.read"))):
        return {"user_id": str(user.id)}

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
                suffix = uuid4().hex[:12]

                user = User(
                    email=f"rbac-{suffix}@example.com",
                    full_name="RBAC Test User",
                    password_hash=hash_password("TestPassword123!"),
                )
                module = SystemModule(
                    code=f"test_{suffix}",
                    name="Test Module",
                    is_enabled=True,
                )
                role = Role(
                    code=f"test_{suffix}",
                    name="Test Role",
                    is_active=True,
                )

                db.add_all([user, module, role])
                db.flush()

                permission = Permission(
                    module_id=module.id,
                    action="read",
                )
                db.add(permission)
                db.flush()

                db.add(RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                ))

                token, _ = create_session(db, user.id)
                db.commit()

                user_id = str(user.id)
                role_id = role.id
                module_id = module.id

            # Use the generated module code in the protected endpoint.
            app.router.routes.clear()

            @app.get("/protected")
            def protected_actual(
                user: User = Depends(
                    require_permission(f"test_{suffix}.read")
                ),
            ):
                return {"user_id": str(user.id)}

            with TestClient(app) as client:
                # No session: 401.
                assert client.get("/protected").status_code == 401

                client.cookies.set("paym_session", token)

                # No assigned role: 403.
                assert client.get("/protected").status_code == 403

                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as db:
                    assignment = UserRoleAssignment(
                        user_id=user.id,
                        role_id=role_id,
                        scope="global",
                    )
                    db.add(assignment)
                    db.commit()
                    assignment_id = assignment.id

                # Valid global role: 200.
                response = client.get("/protected")
                assert response.status_code == 200
                assert response.json()["user_id"] == user_id

                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as db:
                    assignment = db.get(
                        UserRoleAssignment, assignment_id
                    )
                    assignment.revoked_at = datetime.now(timezone.utc)
                    db.commit()

                # Revoked assignment: 403.
                assert client.get("/protected").status_code == 403

                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as db:
                    assignment = db.get(
                        UserRoleAssignment, assignment_id
                    )
                    assignment.revoked_at = None
                    role = db.get(Role, role_id)
                    role.is_active = False
                    db.commit()

                # Inactive role: 403.
                assert client.get("/protected").status_code == 403

                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as db:
                    role = db.get(Role, role_id)
                    role.is_active = True
                    module = db.get(SystemModule, module_id)
                    module.is_enabled = False
                    db.commit()

                # Disabled module: 403.
                assert client.get("/protected").status_code == 403

        finally:
            app.dependency_overrides.clear()
            transaction.rollback()
