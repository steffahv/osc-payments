"""Receipt inputs exclude workflow statuses and client-supplied attribution."""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.master_data.schemas import Input, Page

Amount = Annotated[Decimal, Field(max_digits=18, decimal_places=2, allow_inf_nan=False)]
Consumption = Annotated[Decimal, Field(max_digits=14, decimal_places=3, allow_inf_nan=False)]
Currency = Annotated[str, StringConstraints(min_length=3, max_length=3)]
ReceiptNumber = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ElectricityInput(Input):
    consumption_kwh: Consumption | None = None


class ReceiptFields(Input):
    receipt_number: ReceiptNumber | None = None
    period_start: date | None = None
    period_end: date | None = None
    issue_date: date | None = None
    due_date: date | None = None
    amount: Amount | None = None
    electricity_details: ElectricityInput | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        if "electricity_details" in self.model_fields_set and self.electricity_details is None:
            raise ValueError("Omit electricity_details to leave it unchanged; use consumption_kwh=null to clear consumption")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class ReceiptCreate(ReceiptFields):
    service_account_id: UUID
    currency_code: Currency = "PEN"


class ReceiptUpdate(ReceiptFields):
    service_account_id: UUID | None = None
    currency_code: Currency | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("service_account_id", "currency_code"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ElectricityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    consumption_kwh: Decimal | None


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    service_account_id: UUID
    receipt_number: str | None
    period_start: date | None
    period_end: date | None
    issue_date: date | None
    due_date: date | None
    amount: Decimal | None
    currency_code: str
    status: str
    status_crm: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    electricity_details: ElectricityResponse | None = None


class ReceiptQuery(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
    service_account_id: UUID | None = None
    status: str | None = Field(default=None, min_length=1, max_length=40)
    status_crm: str | None = Field(default=None, min_length=1, max_length=40)
    q: str | None = Field(default=None, min_length=1, max_length=100)
