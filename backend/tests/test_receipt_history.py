"""Stage 3 database tests; all migrations and data remain in rolled-back schemas."""

import importlib.util
import os
from pathlib import Path
from uuid import UUID, uuid4

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import delete, func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.modules.receipts.models import Receipt, ReceiptDocument, ReceiptWorkflowEvent
from app.modules.users.models import User
from test_receipts import account, db as stage_two_db  # noqa: F401 -- reuse isolated fixtures

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]

path = Path(__file__).resolve().parents[1] / "alembic/versions/d39f6b208a14_stage_3_documents_history.py"
spec = importlib.util.spec_from_file_location(path.stem, path)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


@pytest.fixture
def db(stage_two_db):
    with Operations.context(MigrationContext.configure(stage_two_db.connection())):
        migration.upgrade()
    yield stage_two_db


@pytest.fixture
def receipt(db, account):
    receipt = Receipt(service_account_id=account.id)
    db.add(receipt)
    db.flush()
    return receipt


def test_multiple_document_types_and_metadata_defaults(db, receipt):
    for document_type in ("receipt_pdf", "payment_proof", "future_document_type"):
        document = ReceiptDocument(
            receipt_id=receipt.id, document_type=document_type,
            original_filename="receipt.pdf", storage_key="receipts/test/receipt.pdf",
        )
        db.add(document)
        db.flush()
        db.refresh(document)
        assert isinstance(document.id, UUID)
        assert document.uploaded_at.tzinfo is not None
        assert document.uploaded_by is None
        assert document.original_filename == "receipt.pdf"
        assert document.storage_key == "receipts/test/receipt.pdf"
    assert db.scalar(select(func.count()).select_from(ReceiptDocument)) == 3


def test_explicit_status_and_crm_history_does_not_change_receipt(db, receipt):
    for field, old, new in (
        ("status", None, "draft"),
        ("status", "pending", "paid"),
        ("status_crm", "pending", "registered"),
        ("status", "paid", "future_value"),
    ):
        event = ReceiptWorkflowEvent(
            receipt_id=receipt.id, field_name=field, old_value=old, new_value=new,
        )
        db.add(event)
        db.flush()
        db.refresh(event)
        assert isinstance(event.id, UUID)
        assert event.created_at.tzinfo is not None
        assert event.changed_by is None
        assert (event.field_name, event.old_value, event.new_value) == (field, old, new)
    db.refresh(receipt)
    assert (receipt.status, receipt.status_crm) == ("draft", "pending")
    assert db.scalar(select(func.count()).select_from(ReceiptWorkflowEvent)) == 4


def test_receipt_updates_do_not_generate_events(db, receipt):
    receipt.status = "paid"
    receipt.status_crm = "registered"
    db.flush()
    assert db.scalar(select(func.count()).select_from(ReceiptWorkflowEvent)) == 0
    assert db.scalar(select(func.count()).select_from(ReceiptDocument)) == 0


@pytest.mark.parametrize("model,actor_field,values", [
    (ReceiptDocument, "uploaded_by", {
        "document_type": "receipt_pdf", "original_filename": "receipt.pdf", "storage_key": "test/key",
    }),
    (ReceiptWorkflowEvent, "changed_by", {
        "field_name": "status_crm", "old_value": None, "new_value": "registered",
    }),
])
def test_actor_relationships_and_delete_protection(db, receipt, model, actor_field, values):
    actor = User(email="history@example.com", full_name="History author", password_hash="test-only")
    db.add(actor)
    db.flush()
    record = model(receipt_id=receipt.id, **{actor_field: actor.id}, **values)
    db.add(record)
    db.flush()
    assert db.get(User, getattr(record, actor_field)).id == actor.id
    for parent, identifier in ((User, actor.id), (Receipt, receipt.id)):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.execute(delete(parent).where(parent.id == identifier))


@pytest.mark.parametrize("model,field,values", [
    (ReceiptDocument, "receipt_id", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptDocument, "uploaded_by", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptWorkflowEvent, "receipt_id", {"field_name": "status", "new_value": "paid"}),
    (ReceiptWorkflowEvent, "changed_by", {"field_name": "status", "new_value": "paid"}),
])
def test_foreign_keys_reject_missing_references(db, receipt, model, field, values):
    values = {"receipt_id": receipt.id, **values, field: uuid4()}
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(model(**values))
        db.flush()


@pytest.mark.parametrize("model,field,values", [
    (ReceiptDocument, "receipt_id", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptDocument, "document_type", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptDocument, "original_filename", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptDocument, "storage_key", {"document_type": "pdf", "original_filename": "r.pdf", "storage_key": "key"}),
    (ReceiptWorkflowEvent, "receipt_id", {"field_name": "status", "new_value": "paid"}),
    (ReceiptWorkflowEvent, "field_name", {"field_name": "status", "new_value": "paid"}),
    (ReceiptWorkflowEvent, "new_value", {"field_name": "status", "new_value": "paid"}),
])
def test_required_fields(db, receipt, model, field, values):
    values = {"receipt_id": receipt.id, **values, field: None}
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(model(**values))
        db.flush()


def test_migration_matches_models_and_fk_indexes(db):
    context = MigrationContext.configure(db.connection(), opts={
        "compare_type": True, "compare_server_default": True,
    })
    assert compare_metadata(context, Base.metadata) == []
    inspector = inspect(db.connection())
    for table, actor in (("receipt_documents", "uploaded_by"), ("receipt_workflow_events", "changed_by")):
        assert {tuple(index["column_names"]) for index in inspector.get_indexes(table)} == {
            ("receipt_id",), (actor,),
        }
        assert inspector.get_unique_constraints(table) == []


def test_stage_three_downgrade_preserves_receipts(db, receipt):
    connection = db.connection()
    tables = set(inspect(connection).get_table_names())
    receipt_id = receipt.id
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
        assert set(inspect(connection).get_table_names()) == tables - {
            "receipt_documents", "receipt_workflow_events",
        }
        assert db.scalar(select(Receipt.id).where(Receipt.id == receipt_id)) == receipt_id
        migration.upgrade()
    assert set(inspect(connection).get_table_names()) == tables
