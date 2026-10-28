"""Validated master-data inputs and stable response shapes."""
from datetime import datetime
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
NodeCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
SupplyId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
TaxId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Region = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Patch(Input):
    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None and field not in {"tax_id", "region"}:
                raise ValueError(f"{field} cannot be null")
        return self


class NodeCreate(Input):
    code: NodeCode
    name: Name
    node_type_id: UUID
    is_active: bool = True


class NodeUpdate(Patch):
    code: NodeCode | None = None
    name: Name | None = None
    node_type_id: UUID | None = None
    is_active: bool | None = None


class ProviderCreate(Input):
    name: Name
    tax_id: TaxId | None = None
    region: Region | None = None
    is_active: bool = True


class ProviderUpdate(Patch):
    name: Name | None = None
    tax_id: TaxId | None = None
    region: Region | None = None
    is_active: bool | None = None


class ServiceAccountCreate(Input):
    node_id: UUID
    provider_id: UUID
    utility_type_id: UUID
    supply_id: SupplyId
    is_active: bool = True


class ServiceAccountUpdate(Patch):
    node_id: UUID | None = None
    provider_id: UUID | None = None
    utility_type_id: UUID | None = None
    supply_id: SupplyId | None = None
    is_active: bool | None = None


class RecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CatalogResponse(RecordResponse):
    code: str
    name: str


class NodeResponse(CatalogResponse):
    node_type_id: UUID


class ProviderResponse(RecordResponse):
    name: str
    tax_id: str | None
    region: str | None


class ServiceAccountResponse(RecordResponse):
    node_id: UUID
    provider_id: UUID
    utility_type_id: UUID
    supply_id: str


class ListQuery(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
    is_active: bool | None = None
    q: str | None = Field(default=None, min_length=1, max_length=200)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
