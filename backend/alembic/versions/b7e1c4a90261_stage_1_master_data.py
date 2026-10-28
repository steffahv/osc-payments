"""Stage 1 utility catalogs, nodes, providers, and service accounts.

Revision ID: b7e1c4a90261
Revises: ced18c17b404
"""

from uuid import UUID

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

revision = "b7e1c4a90261"
down_revision = "ced18c17b404"
branch_labels = None
depends_on = None


def seed_catalogs() -> None:
    """Insert initial codes without overwriting existing names or active flags."""
    utility_types = sa.table(
        "utility_types", sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(30)), sa.column("name", sa.String(100)),
    )
    node_types = sa.table(
        "node_types", sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(20)), sa.column("name", sa.String(100)),
    )
    op.execute(insert(utility_types).values(
        id=UUID("3752ed3d-7416-4a86-b2ec-07380ea41f68"),
        code="electricity", name="Electricity",
    ).on_conflict_do_nothing(index_elements=["code"]))
    op.execute(insert(node_types).values([
        {"id": UUID("226ff13a-d8bc-4b59-a841-b21b4ad5839b"), "code": "TX", "name": "Transport"},
        {"id": UUID("41374c13-17b0-4ae8-bbf2-0c6211641233"), "code": "AX", "name": "Access"},
        {"id": UUID("97ec39c1-a9a1-4555-b1f8-5bb55d8438ce"), "code": "MC", "name": "Definition pending"},
    ]).on_conflict_do_nothing(index_elements=["code"]))


def upgrade() -> None:
    op.create_table(
        "utility_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utility_types")),
        sa.UniqueConstraint("code", name=op.f("uq_utility_types_code")),
    )
    op.create_table(
        "node_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_node_types")),
        sa.UniqueConstraint("code", name=op.f("uq_node_types_code")),
    )
    op.create_table(
        "nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("node_type_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["node_type_id"], ["node_types.id"], ondelete="RESTRICT",
                                name=op.f("fk_nodes_node_type_id_node_types")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nodes")),
    )
    op.create_index(op.f("ix_nodes_code"), "nodes", ["code"])
    op.create_index(op.f("ix_nodes_node_type_id"), "nodes", ["node_type_id"])
    op.create_table(
        "providers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tax_id", sa.String(20), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_providers")),
    )
    op.create_table(
        "service_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("utility_type_id", sa.Uuid(), nullable=False),
        sa.Column("supply_id", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="RESTRICT",
                                name=op.f("fk_service_accounts_node_id_nodes")),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"], ondelete="RESTRICT",
                                name=op.f("fk_service_accounts_provider_id_providers")),
        sa.ForeignKeyConstraint(["utility_type_id"], ["utility_types.id"], ondelete="RESTRICT",
                                name=op.f("fk_service_accounts_utility_type_id_utility_types")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_accounts")),
    )
    for column in ("node_id", "provider_id", "utility_type_id", "supply_id"):
        op.create_index(op.f(f"ix_service_accounts_{column}"), "service_accounts", [column])
    seed_catalogs()


def downgrade() -> None:
    # Explicit rollback only: dependent tables must be removed before their masters.
    op.drop_table("service_accounts")
    op.drop_table("providers")
    op.drop_table("nodes")
    op.drop_table("node_types")
    op.drop_table("utility_types")
