from uuid import UUID
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin

class Permission(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("module_id", "action"),
        CheckConstraint("action ~ '^[a-z][a-z0-9_]*$'", name="valid_action"),
    )
    module_id: Mapped[UUID] = mapped_column(ForeignKey("system_modules.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
