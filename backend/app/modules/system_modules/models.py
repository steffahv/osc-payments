from sqlalchemy import Boolean, CheckConstraint, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin

class SystemModule(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "system_modules"
    __table_args__ = (CheckConstraint("code ~ '^[a-z][a-z0-9_]*$'", name="valid_code"),)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
