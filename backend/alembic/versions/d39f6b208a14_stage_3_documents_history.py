"""Stage 3 receipt document metadata and workflow history.

Revision ID: d39f6b208a14
Revises: c2d8a9410e73
"""

from alembic import op
import sqlalchemy as sa

revision = "d39f6b208a14"
down_revision = "c2d8a9410e73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "receipt_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("receipt_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipt_documents")),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipt_documents_receipt_id_receipts")),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipt_documents_uploaded_by_users")),
    )
    op.create_index(op.f("ix_receipt_documents_receipt_id"), "receipt_documents", ["receipt_id"])
    op.create_index(op.f("ix_receipt_documents_uploaded_by"), "receipt_documents", ["uploaded_by"])
    op.create_table(
        "receipt_workflow_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("receipt_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(40), nullable=False),
        sa.Column("old_value", sa.String(100), nullable=True),
        sa.Column("new_value", sa.String(100), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipt_workflow_events")),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipt_workflow_events_receipt_id_receipts")),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_receipt_workflow_events_changed_by_users")),
    )
    op.create_index(op.f("ix_receipt_workflow_events_receipt_id"), "receipt_workflow_events", ["receipt_id"])
    op.create_index(op.f("ix_receipt_workflow_events_changed_by"), "receipt_workflow_events", ["changed_by"])


def downgrade() -> None:
    op.drop_table("receipt_workflow_events")
    op.drop_table("receipt_documents")
