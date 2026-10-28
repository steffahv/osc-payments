"""Atomic receipt/detail persistence, with no workflow or history side effects."""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.master_data.models import ServiceAccount, UtilityType
from app.modules.receipts.models import ElectricityReceiptDetails, Receipt
from app.modules.receipts.schemas import ElectricityResponse, ReceiptQuery, ReceiptResponse


def serialize(receipt: Receipt, details: ElectricityReceiptDetails | None) -> ReceiptResponse:
    response = ReceiptResponse.model_validate(receipt)
    if details is not None:
        response.electricity_details = ElectricityResponse.model_validate(details)
    return response


def get_receipt(db: Session, receipt_id: UUID) -> ReceiptResponse:
    row = db.execute(select(Receipt, ElectricityReceiptDetails).outerjoin(
        ElectricityReceiptDetails, ElectricityReceiptDetails.receipt_id == Receipt.id,
    ).where(Receipt.id == receipt_id)).first()
    if row is None:
        raise HTTPException(404, "Record not found")
    return serialize(*row)


def list_receipts(db: Session, query: ReceiptQuery):
    conditions = []
    for field in ("service_account_id", "status", "status_crm"):
        value = getattr(query, field)
        if value is not None:
            conditions.append(getattr(Receipt, field) == value)
    if query.q is not None:
        conditions.append(Receipt.receipt_number.icontains(query.q, autoescape=True))
    total = db.scalar(select(func.count()).select_from(Receipt).where(*conditions))
    rows = db.execute(select(Receipt, ElectricityReceiptDetails).outerjoin(
        ElectricityReceiptDetails, ElectricityReceiptDetails.receipt_id == Receipt.id,
    ).where(*conditions).order_by(Receipt.id).offset(query.offset).limit(query.limit)).all()
    return {"items": [serialize(*row) for row in rows], "total": total,
            "offset": query.offset, "limit": query.limit}


def save_receipt(db: Session, values: dict, *, actor_id: UUID | None = None,
                 receipt_id: UUID | None = None) -> ReceiptResponse:
    try:
        if receipt_id is None:
            receipt = Receipt(created_by=actor_id)
        else:
            # Serialize updates so merged dates and utility/details remain consistent.
            receipt = db.scalar(select(Receipt).where(Receipt.id == receipt_id).with_for_update())
            if receipt is None:
                raise HTTPException(404, "Record not found")
        details = db.get(ElectricityReceiptDetails, receipt.id) if receipt_id else None
        account_id = values.get("service_account_id", receipt.service_account_id)
        utility_code = db.scalar(select(UtilityType.code).join(
            ServiceAccount, ServiceAccount.utility_type_id == UtilityType.id,
        ).where(ServiceAccount.id == account_id))
        if utility_code is None:
            raise HTTPException(422, "service_account_id references a missing record")
        start = values.get("period_start", receipt.period_start)
        end = values.get("period_end", receipt.period_end)
        if start and end and end < start:
            raise HTTPException(422, "period_end must be on or after period_start")
        if (details is not None or "electricity_details" in values) and utility_code != "electricity":
            raise HTTPException(422, "Electricity details require an electricity service account")
        detail_values = values.pop("electricity_details", None)
        for field, value in values.items():
            setattr(receipt, field, value)
        db.add(receipt)
        db.flush()
        if detail_values is not None:
            if details is None:
                details = ElectricityReceiptDetails(receipt_id=receipt.id)
            for field, value in detail_values.items():
                setattr(details, field, value)
            db.add(details)
            # Updating only utility details should also mark the receipt as updated.
            receipt.updated_at = func.now()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Operation conflicts with related data") from None
    except Exception:
        db.rollback()
        raise
    return get_receipt(db, receipt.id)
