from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text, func, text, true
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin

class Role(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (CheckConstraint("code ~ '^[a-z][a-z0-9_]*$'", name="valid_code"),)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id", ondelete="RESTRICT"), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserRoleAssignment(IdentityMixin, Base):
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        CheckConstraint("(scope = 'global' AND team_id IS NULL) OR (scope = 'team' AND team_id IS NOT NULL)", name="scope_team"),
        CheckConstraint("revoked_at IS NULL OR revoked_at >= created_at", name="revocation_time"),
        ForeignKeyConstraint(["user_id", "team_id"], ["team_memberships.user_id", "team_memberships.team_id"], name="fk_assignments_membership", ondelete="RESTRICT"),
        Index("uq_assignments_active_global", "user_id", "role_id", unique=True, postgresql_where=text("scope = 'global' AND revoked_at IS NULL")),
        Index("uq_assignments_active_team", "user_id", "role_id", "team_id", unique=True, postgresql_where=text("scope = 'team' AND revoked_at IS NULL")),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    scope: Mapped[str] = mapped_column(String(16))
    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), index=True)
    assigned_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
