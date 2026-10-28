"""Small shared database operations for the three master-data resources."""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.master_data.models import Node, NodeType, Provider, UtilityType
from app.modules.master_data.schemas import ListQuery

REFERENCES = {
    "node_type_id": NodeType, "node_id": Node,
    "provider_id": Provider, "utility_type_id": UtilityType,
}


def get_record(db: Session, model, record_id: UUID):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


def list_records(db: Session, model, query: ListQuery, search_columns, **filters):
    conditions = [getattr(model, key) == value for key, value in filters.items() if value is not None]
    if query.is_active is not None:
        conditions.append(model.is_active == query.is_active)
    if query.q is not None:
        conditions.append(or_(*(column.icontains(query.q, autoescape=True) for column in search_columns)))
    total = db.scalar(select(func.count()).select_from(model).where(*conditions))
    items = db.scalars(select(model).where(*conditions).order_by(model.id)
                       .offset(query.offset).limit(query.limit)).all()
    return {"items": items, "total": total, "offset": query.offset, "limit": query.limit}


def save_record(db: Session, record, values: dict):
    for field, value in values.items():
        if field in REFERENCES and db.get(REFERENCES[field], value) is None:
            raise HTTPException(422, f"{field} references a missing record")
    for field, value in values.items():
        setattr(record, field, value)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handles concurrent FK changes without exposing SQL or submitted values.
        raise HTTPException(409, "Operation conflicts with related data") from None
    db.refresh(record)
    return record
