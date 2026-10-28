"""Receipt management with explicit, independent global permission checks."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.permissions.dependencies import require_permission
from app.modules.receipts.schemas import Page, ReceiptCreate, ReceiptUpdate, ReceiptQuery, ReceiptResponse
from app.modules.receipts.service import get_receipt, list_receipts, save_receipt
from app.modules.users.models import User

router = APIRouter(prefix="/receipts", tags=["Receipts"])
Db = Annotated[Session, Depends(get_db)]


@router.post("", response_model=ReceiptResponse, status_code=201)
def create_receipt(data: ReceiptCreate, db: Db,
                   user: Annotated[User, Depends(require_permission("receipts.create"))]):
    return save_receipt(db, data.model_dump(exclude_unset=True), actor_id=user.id)


@router.get("", response_model=Page[ReceiptResponse], dependencies=[Depends(require_permission("receipts.view"))])
def read_receipts(db: Db, query: Annotated[ReceiptQuery, Depends()]):
    return list_receipts(db, query)


@router.get("/{receipt_id}", response_model=ReceiptResponse, dependencies=[Depends(require_permission("receipts.view"))])
def read_receipt(receipt_id: UUID, db: Db):
    return get_receipt(db, receipt_id)


@router.patch("/{receipt_id}", response_model=ReceiptResponse, dependencies=[Depends(require_permission("receipts.update"))])
def update_receipt(receipt_id: UUID, data: ReceiptUpdate, db: Db):
    return save_receipt(db, data.model_dump(exclude_unset=True), receipt_id=receipt_id)
