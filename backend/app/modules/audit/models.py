from datetime import datetime
from uuid import UUID
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.mixins import IdentityMixin

class AuditLog(IdentityMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("result IN ('success', 'failure')", name="result"),
        Index("ix_audit_actor_time", "actor_user_id", "occurred_at"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[UUID | None]
    result: Mapped[str] = mapped_column(String(16))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    request_id: Mapped[UUID] = mapped_column(index=True)
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"))
