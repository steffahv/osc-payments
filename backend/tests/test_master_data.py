"""Stage 1 PostgreSQL tests in a temporary schema, rolled back after each test."""

import importlib.util
import os
from pathlib import Path
from uuid import UUID, uuid4

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import MetaData, delete, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.modules.master_data.models import Node, NodeType, Provider, ServiceAccount, UtilityType

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1"),
]

MODELS = (UtilityType, NodeType, Node, Provider, ServiceAccount)
revision_path = Path(__file__).resolve().parents[1] / "alembic/versions/b7e1c4a90261_stage_1_master_data.py"
spec = importlib.util.spec_from_file_location("stage_one_migration", revision_path)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


@pytest.fixture
def db():
    # Never downgrade or truncate the application's schema. PostgreSQL rolls back DDL.
    with get_engine().connect() as connection:
        transaction = connection.begin()
        schema = "stage_one_test_" + uuid4().hex
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture
def account(db):
    node_type = db.scalar(select(NodeType).where(NodeType.code == "TX"))
    utility = db.scalar(select(UtilityType).where(UtilityType.code == "electricity"))
    node = Node(code="T4249", name="T4249_SM_SANTA LUCIA", node_type_id=node_type.id)
    provider = Provider(name="Test provider")
    db.add_all([node, provider])
    db.flush()
    account = ServiceAccount(
        node_id=node.id, provider_id=provider.id, utility_type_id=utility.id,
        supply_id="001234567",
    )
    db.add(account)
    db.flush()
    return account


def test_catalog_seed_is_repeatable_and_preserves_existing_values(db):
    tx = db.scalar(select(NodeType).where(NodeType.code == "TX"))
    tx.is_active = False
    db.flush()
    with Operations.context(MigrationContext.configure(db.connection())):
        migration.seed_catalogs()
    assert db.execute(select(UtilityType.code, UtilityType.name)).all() == [
        ("electricity", "Electricity"),
    ]
    assert dict(db.execute(select(NodeType.code, NodeType.name)).all()) == {
        "TX": "Transport", "AX": "Access", "MC": "Definition pending",
    }
    db.refresh(tx)
    assert tx.is_active is False


def test_migration_matches_models_and_indexes(db):
    metadata = MetaData()
    for model in MODELS:
        model.__table__.to_metadata(metadata)
    context = MigrationContext.configure(db.connection(), opts={
        "compare_type": True, "compare_server_default": True,
    })
    assert compare_metadata(context, metadata) == []
    inspector = inspect(db.connection())
    assert {index["column_names"][0] for index in inspector.get_indexes("service_accounts")} == {
        "node_id", "provider_id", "utility_type_id", "supply_id",
    }
    assert inspector.get_unique_constraints("service_accounts") == []


def test_multiple_accounts_preserve_supply_id_and_allow_deactivation(db, account):
    duplicate = ServiceAccount(
        node_id=account.node_id, provider_id=account.provider_id,
        utility_type_id=account.utility_type_id, supply_id=account.supply_id,
    )
    db.add(duplicate)
    db.flush()
    assert duplicate.id != account.id
    db.refresh(account)
    assert account.supply_id == "001234567"
    for model in MODELS:
        record = db.scalars(select(model)).first()
        assert isinstance(record.id, UUID)
        assert record.is_active is True
        assert record.created_at.tzinfo is not None
        assert record.updated_at.tzinfo is not None
        record.is_active = False
    db.flush()
    assert db.scalar(select(func.count()).select_from(ServiceAccount)) == 2
    assert db.get(ServiceAccount, account.id).is_active is False


@pytest.mark.parametrize("model,code", [(UtilityType, "electricity"), (NodeType, "TX")])
def test_catalog_codes_are_unique(db, model, code):
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(model(code=code, name="Duplicate"))
        db.flush()


@pytest.mark.parametrize("field", ["node_id", "provider_id", "utility_type_id"])
def test_service_account_foreign_keys(db, account, field):
    values = {
        "node_id": account.node_id, "provider_id": account.provider_id,
        "utility_type_id": account.utility_type_id, "supply_id": "0002",
    }
    values[field] = uuid4()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(ServiceAccount(**values))
        db.flush()


def test_node_type_foreign_key(db):
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(Node(code="T4249", name="Test node", node_type_id=uuid4()))
        db.flush()


@pytest.mark.parametrize("model", [Node, Provider, UtilityType, NodeType])
def test_referenced_masters_cannot_be_deleted(db, account, model):
    identifiers = {
        Node: account.node_id, Provider: account.provider_id,
        UtilityType: account.utility_type_id,
        NodeType: db.get(Node, account.node_id).node_type_id,
    }
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(delete(model).where(model.id == identifiers[model]))


def test_unconfirmed_unique_rules_are_not_enforced(db, account):
    node = db.get(Node, account.node_id)
    db.add(Node(code=node.code, name="Another source row", node_type_id=node.node_type_id))
    db.add_all([
        Provider(name="Provider A", tax_id="000123"),
        Provider(name="Provider B", tax_id="000123"),
    ])
    db.flush()
    assert db.scalar(select(func.count()).select_from(Node)) == 2


def test_migration_downgrade_and_upgrade_in_isolated_schema(db):
    with Operations.context(MigrationContext.configure(db.connection())):
        migration.downgrade()
        assert inspect(db.connection()).get_table_names() == []
        migration.upgrade()
    assert set(inspect(db.connection()).get_table_names()) == {
        model.__tablename__ for model in MODELS
    }
    assert db.scalar(select(func.count()).select_from(NodeType)) == 3
