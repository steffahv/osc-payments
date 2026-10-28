"""Stage 2 receipts and electricity receipt details.

Revision ID: c2d8a9410e73
Revises: b7e1c4a90261
"""

from alembic import op
import sqlalchemy as sa

revision = "c2d8a9410e73"
down_revision = "b7e1c4a90261"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "receipts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("service_account_id", sa.Uuid(), nullable=False),
        sa.Column("receipt_number", sa.String(100), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency_code", sa.CHAR(3), server_default=sa.text("'PEN'"), nullable=False),
        sa.Column("status", sa.String(40), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("status_crm", sa.String(40), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("period_end >= period_start", name=op.f("ck_receipts_period_order")),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipts_service_account_id_service_accounts")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipts_created_by_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipts")),
    )
    op.create_index(op.f("ix_receipts_service_account_id"), "receipts", ["service_account_id"])
    op.create_index(op.f("ix_receipts_created_by"), "receipts", ["created_by"])
    op.create_table(
        "electricity_receipt_details",
        sa.Column("receipt_id", sa.Uuid(), nullable=False),
        sa.Column("consumption_kwh", sa.Numeric(14, 3), nullable=True),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="RESTRICT",
                                name=op.f("fk_electricity_receipt_details_receipt_id_receipts")),
        sa.PrimaryKeyConstraint("receipt_id", name=op.f("pk_electricity_receipt_details")),
    )


def downgrade() -> None:
    op.drop_table("electricity_receipt_details")
    op.drop_table("receipts")
