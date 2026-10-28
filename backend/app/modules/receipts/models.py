"""Receipt drafts, electricity details, document metadata, and explicit history."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CHAR, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin


class Receipt(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "receipts"
    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="period_order"),
    )

    service_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_accounts.id", ondelete="RESTRICT"), index=True,
    )
    receipt_number: Mapped[str | None] = mapped_column(String(100))
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    issue_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency_code: Mapped[str] = mapped_column(CHAR(3), default="PEN", server_default=text("'PEN'"))
    # Workflow values are provisional; application transitions belong to a later stage.
    status: Mapped[str] = mapped_column(String(40), default="draft", server_default=text("'draft'"))
    status_crm: Mapped[str] = mapped_column(String(40), default="pending", server_default=text("'pending'"))
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True,
    )


class ElectricityReceiptDetails(Base):
    __tablename__ = "electricity_receipt_details"

    receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="RESTRICT"), primary_key=True,
    )
    consumption_kwh: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))


class ReceiptDocument(IdentityMixin, Base):
    """Document metadata only; storage and upload behavior are implemented later."""

    __tablename__ = "receipt_documents"

    receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="RESTRICT"), index=True,
    )
    document_type: Mapped[str] = mapped_column(String(40))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(Text)
    uploaded_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class ReceiptWorkflowEvent(IdentityMixin, Base):
    """Explicit history records; inserting one does not change the receipt."""

    __tablename__ = "receipt_workflow_events"

    receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="RESTRICT"), index=True,
    )
    field_name: Mapped[str] = mapped_column(String(40))
    old_value: Mapped[str | None] = mapped_column(String(100))
    new_value: Mapped[str] = mapped_column(String(100))
    changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
