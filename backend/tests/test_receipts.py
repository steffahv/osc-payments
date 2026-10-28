"""Receipt schema tests using real migrations in rolled-back PostgreSQL schemas."""

import importlib.util
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import delete, inspect, select, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.db import models  # noqa: F401 -- register all migration metadata
from app.db.base import Base
from app.db.session import get_engine
from app.modules.master_data.models import Node, NodeType, Provider, ServiceAccount, UtilityType
from app.modules.receipts.models import ElectricityReceiptDetails, Receipt
from app.modules.users.models import User

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]

MIGRATIONS = []
for filename in (
    "ced18c17b404_initial_auth_schema.py",
    "b7e1c4a90261_stage_1_master_data.py",
    "c2d8a9410e73_stage_2_receipts.py",
):
    path = Path(__file__).resolve().parents[1] / "alembic/versions" / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    MIGRATIONS.append(migration)


@pytest.fixture
def db():
    with get_engine().connect() as connection:
        transaction = connection.begin()
        schema = "receipts_test_" + uuid4().hex
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            with Operations.context(MigrationContext.configure(connection)):
                for migration in MIGRATIONS:
                    migration.upgrade()
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            # Includes all DDL: no application records or schemas are removed.
            transaction.rollback()


@pytest.fixture
def account(db):
    node = Node(
        code="T4249", name="T4249_SM_SANTA LUCIA",
        node_type_id=db.scalar(select(NodeType.id).where(NodeType.code == "TX")),
    )
    provider = Provider(name="Receipt test provider")
    db.add_all([node, provider])
    db.flush()
    account = ServiceAccount(
        node_id=node.id, provider_id=provider.id, supply_id="001234567",
        utility_type_id=db.scalar(select(UtilityType.id).where(UtilityType.code == "electricity")),
    )
    db.add(account)
    db.flush()
    return account


def test_nullable_draft_and_orm_defaults(db, account):
    receipt = Receipt(service_account_id=account.id)
    db.add(receipt)
    db.flush()
    details = ElectricityReceiptDetails(receipt_id=receipt.id)
    db.add(details)
    db.flush()
    db.refresh(receipt)
    assert isinstance(receipt.id, UUID)
    assert (receipt.currency_code, receipt.status, receipt.status_crm) == ("PEN", "draft", "pending")
    for field in ("receipt_number", "period_start", "period_end", "issue_date", "due_date", "amount", "created_by"):
        assert getattr(receipt, field) is None
    assert details.consumption_kwh is None
    assert receipt.created_at.tzinfo is not None
    assert receipt.updated_at.tzinfo is not None


def test_database_defaults_without_orm(db, account):
    values = db.execute(text(
        "INSERT INTO receipts (id, service_account_id) VALUES (:id, :account) "
        "RETURNING currency_code, status, status_crm, created_at, updated_at"
    ), {"id": uuid4(), "account": account.id}).one()
    assert values[:3] == ("PEN", "draft", "pending")
    assert values.created_at.tzinfo is not None
    assert values.updated_at.tzinfo is not None


@pytest.mark.parametrize("start,end,valid", [
    (None, None, True),
    (date(2026, 10, 1), None, True),
    (None, date(2026, 10, 31), True),
    (date(2026, 10, 1), date(2026, 10, 31), True),
    (date(2026, 10, 1), date(2026, 10, 1), True),
    (date(2026, 10, 31), date(2026, 10, 1), False),
])
def test_billing_period_order(db, account, start, end, valid):
    receipt = Receipt(service_account_id=account.id, period_start=start, period_end=end)
    if not valid:
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(receipt)
            db.flush()
    else:
        db.add(receipt)
        db.flush()
        db.refresh(receipt)
        assert (receipt.period_start, receipt.period_end) == (start, end)


@pytest.mark.parametrize("amount,kwh,stored_amount,stored_kwh", [
    ("1234567890123456.78", "12345678901.234", "1234567890123456.78", "12345678901.234"),
    ("12.345", "45.6789", "12.35", "45.679"),
    ("0", "0", "0.00", "0.000"),
])
def test_numeric_precision_and_postgresql_rounding(db, account, amount, kwh, stored_amount, stored_kwh):
    receipt = Receipt(service_account_id=account.id, amount=Decimal(amount))
    db.add(receipt)
    db.flush()
    details = ElectricityReceiptDetails(receipt_id=receipt.id, consumption_kwh=Decimal(kwh))
    db.add(details)
    db.flush()
    db.refresh(receipt)
    db.refresh(details)
    assert receipt.amount == Decimal(stored_amount)
    assert details.consumption_kwh == Decimal(stored_kwh)
    assert receipt.amount.as_tuple().exponent == -2
    assert details.consumption_kwh.as_tuple().exponent == -3


@pytest.mark.parametrize("field", ["amount", "consumption_kwh"])
def test_numeric_overflow_rejected(db, account, field):
    receipt = Receipt(service_account_id=account.id)
    db.add(receipt)
    db.flush()
    with pytest.raises(DataError), db.begin_nested():
        if field == "amount":
            receipt.amount = Decimal("10000000000000000.00")
        else:
            db.add(ElectricityReceiptDetails(
                receipt_id=receipt.id, consumption_kwh=Decimal("100000000000.000"),
            ))
        db.flush()


@pytest.mark.parametrize("field", ["service_account_id", "created_by", "receipt_id"])
def test_foreign_keys(db, account, field):
    with pytest.raises(IntegrityError), db.begin_nested():
        if field == "receipt_id":
            db.add(ElectricityReceiptDetails(receipt_id=uuid4()))
        else:
            values = {"service_account_id": account.id, field: uuid4()}
            db.add(Receipt(**values))
        db.flush()


def test_creator_and_reference_delete_protection(db, account):
    user = User(email="receipt-author@example.com", full_name="Test author", password_hash="test-only")
    db.add(user)
    db.flush()
    receipt = Receipt(service_account_id=account.id, created_by=user.id)
    db.add(receipt)
    db.flush()
    assert db.get(User, receipt.created_by).email == user.email
    for model, identifier in ((User, user.id), (ServiceAccount, account.id)):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.execute(delete(model).where(model.id == identifier))


def test_electricity_details_are_optional_and_one_to_one(db, account):
    receipt = Receipt(service_account_id=account.id)
    db.add(receipt)
    db.flush()
    assert db.get(ElectricityReceiptDetails, receipt.id) is None
    db.add(ElectricityReceiptDetails(receipt_id=receipt.id))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(text("INSERT INTO electricity_receipt_details (receipt_id) VALUES (:id)"), {"id": receipt.id})
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(delete(Receipt).where(Receipt.id == receipt.id))


def test_duplicates_and_independent_provisional_statuses(db, account):
    for status, crm in (("paid", "pending"), ("draft", "registered"), ("future_status", "future_crm")):
        db.add(Receipt(
            service_account_id=account.id, receipt_number="R-001",
            period_start=date(2026, 10, 1), period_end=date(2026, 10, 31),
            issue_date=date(2026, 10, 2), due_date=date(2026, 11, 1),
            status=status, status_crm=crm,
        ))
    db.flush()
    rows = db.scalars(select(Receipt)).all()
    assert len(rows) == 3
    assert {(row.status, row.status_crm) for row in rows} == {
        ("paid", "pending"), ("draft", "registered"), ("future_status", "future_crm"),
    }
    assert all(row.issue_date == date(2026, 10, 2) and row.due_date == date(2026, 11, 1) for row in rows)


def test_schema_matches_models_and_has_only_relationship_indexes(db):
    context = MigrationContext.configure(db.connection(), opts={
        "compare_type": True, "compare_server_default": True,
    })
    assert compare_metadata(context, Base.metadata) == []
    inspector = inspect(db.connection())
    assert {tuple(index["column_names"]) for index in inspector.get_indexes("receipts")} == {
        ("service_account_id",), ("created_by",),
    }
    assert inspector.get_unique_constraints("receipts") == []
    assert inspector.get_pk_constraint("electricity_receipt_details")["constrained_columns"] == ["receipt_id"]


def test_stage_two_downgrade_preserves_prior_tables_and_data(db, account):
    connection = db.connection()
    before = set(inspect(connection).get_table_names())
    with Operations.context(MigrationContext.configure(connection)):
        MIGRATIONS[-1].downgrade()
        assert set(inspect(connection).get_table_names()) == before - {"receipts", "electricity_receipt_details"}
        assert db.scalar(select(ServiceAccount.id).where(ServiceAccount.id == account.id)) == account.id
        MIGRATIONS[-1].upgrade()
    assert set(inspect(connection).get_table_names()) == before
