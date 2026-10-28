"""Register the v1 module permission catalog without granting access.

Revision ID: e4a109bc7283
Revises: d39f6b208a14
"""
from uuid import UUID, uuid5

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

revision = "e4a109bc7283"
down_revision = "d39f6b208a14"
branch_labels = None
depends_on = None

NAMESPACE = UUID("b0d6a0d6-a331-4b2e-8b77-567fbd0bccf7")
CATALOG = {
    "dashboard": ("Dashboard", ("view",)),
    "receipts": ("Receipt Management", ("view", "create", "update")),
    "reports": ("Reports", ("view", "export")),
    "master_data": ("Master Data", ("view", "manage")),
    "admin": ("Administration", ("users_manage", "roles_manage")),
}


def upgrade() -> None:
    modules = sa.table("system_modules",
        sa.column("id", sa.Uuid()), sa.column("code", sa.String(80)),
        sa.column("name", sa.String(120)))
    permissions = sa.table("permissions",
        sa.column("id", sa.Uuid()), sa.column("module_id", sa.Uuid()),
        sa.column("action", sa.String(80)))
    for code, (name, actions) in CATALOG.items():
        op.execute(insert(modules).values(
            id=uuid5(NAMESPACE, code), code=code, name=name,
        ).on_conflict_do_nothing(index_elements=["code"]))
        # Resolve existing module IDs instead of assuming the deterministic seed ID.
        module_id = sa.select(modules.c.id).where(modules.c.code == code).scalar_subquery()
        for action in actions:
            op.execute(insert(permissions).values(
                id=uuid5(NAMESPACE, f"{code}.{action}"), module_id=module_id, action=action,
            ).on_conflict_do_nothing(index_elements=["module_id", "action"]))


def downgrade() -> None:
    # Retain shared catalog entries: they may predate this seed or now be assigned.
    # Reapplying upgrade is idempotent; no role permissions or assignments are removed.
    pass
