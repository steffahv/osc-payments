from uuid import UUID
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin

class Team(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (CheckConstraint("code ~ '^[a-z][a-z0-9_]*$'", name="valid_code"),)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

class TeamMembership(TimestampMixin, Base):
    __tablename__ = "team_memberships"
    __table_args__ = (Index("ix_team_memberships_team_active", "team_id", "is_active"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
