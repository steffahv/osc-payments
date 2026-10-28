"""Stage 1 master data. Deactivate records rather than deleting their history."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin, TimestampMixin


class UtilityType(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "utility_types"

    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class NodeType(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "node_types"

    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class Node(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "nodes"

    # Code and name are independent source fields; code uniqueness is unconfirmed.
    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(200))
    node_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("node_types.id", ondelete="RESTRICT"), index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class Provider(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(200))
    tax_id: Mapped[str | None] = mapped_column(String(20))
    region: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class ServiceAccount(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "service_accounts"

    node_id: Mapped[UUID] = mapped_column(
        ForeignKey("nodes.id", ondelete="RESTRICT"), index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"), index=True,
    )
    utility_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("utility_types.id", ondelete="RESTRICT"), index=True,
    )
    # Keep leading zeros. No supply uniqueness rule until actual data is reviewed.
    supply_id: Mapped[str] = mapped_column(String(100), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
