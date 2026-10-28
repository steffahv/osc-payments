"""Global-permission master-data APIs. No team grants or hard deletion."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.permissions.dependencies import require_permission
from app.modules.master_data.models import UtilityType, NodeType, Node, Provider, ServiceAccount
from app.modules.master_data.schemas import (
    CatalogResponse, NodeCreate, NodeUpdate, NodeResponse,
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse, ListQuery, Page,
)
from app.modules.master_data.service import get_record, list_records, save_record

router = APIRouter(prefix="/master-data", tags=["Master Data"])
Db = Annotated[Session, Depends(get_db)]
Filters = Annotated[ListQuery, Depends()]
READ = [Depends(require_permission("master_data.view"))]
WRITE = [Depends(require_permission("master_data.manage"))]


@router.get("/utility-types", response_model=Page[CatalogResponse], dependencies=READ)
def list_utility_types(db: Db, query: Filters):
    return list_records(db, UtilityType, query, (UtilityType.code, UtilityType.name,))


@router.get("/utility-types/{record_id}", response_model=CatalogResponse, dependencies=READ)
def get_utility_types(record_id: UUID, db: Db):
    return get_record(db, UtilityType, record_id)


@router.get("/node-types", response_model=Page[CatalogResponse], dependencies=READ)
def list_node_types(db: Db, query: Filters):
    return list_records(db, NodeType, query, (NodeType.code, NodeType.name,))


@router.get("/node-types/{record_id}", response_model=CatalogResponse, dependencies=READ)
def get_node_types(record_id: UUID, db: Db):
    return get_record(db, NodeType, record_id)


@router.get("/nodes", response_model=Page[NodeResponse], dependencies=READ)
def list_nodes(db: Db, query: Filters, node_type_id: UUID | None = None):
    return list_records(db, Node, query, (Node.code, Node.name,), node_type_id=node_type_id)


@router.get("/nodes/{record_id}", response_model=NodeResponse, dependencies=READ)
def get_nodes(record_id: UUID, db: Db):
    return get_record(db, Node, record_id)


@router.post("/nodes", response_model=NodeResponse, status_code=201, dependencies=WRITE)
def create_nodes(data: NodeCreate, db: Db):
    return save_record(db, Node(), data.model_dump())


@router.patch("/nodes/{record_id}", response_model=NodeResponse, dependencies=WRITE)
def update_nodes(record_id: UUID, data: NodeUpdate, db: Db):
    return save_record(db, get_record(db, Node, record_id), data.model_dump(exclude_unset=True))


@router.get("/providers", response_model=Page[ProviderResponse], dependencies=READ)
def list_providers(db: Db, query: Filters):
    return list_records(db, Provider, query, (Provider.name, Provider.tax_id, Provider.region,))


@router.get("/providers/{record_id}", response_model=ProviderResponse, dependencies=READ)
def get_providers(record_id: UUID, db: Db):
    return get_record(db, Provider, record_id)


@router.post("/providers", response_model=ProviderResponse, status_code=201, dependencies=WRITE)
def create_providers(data: ProviderCreate, db: Db):
    return save_record(db, Provider(), data.model_dump())


@router.patch("/providers/{record_id}", response_model=ProviderResponse, dependencies=WRITE)
def update_providers(record_id: UUID, data: ProviderUpdate, db: Db):
    return save_record(db, get_record(db, Provider, record_id), data.model_dump(exclude_unset=True))


@router.get("/service-accounts", response_model=Page[ServiceAccountResponse], dependencies=READ)
def list_service_accounts(db: Db, query: Filters, node_id: UUID | None = None, provider_id: UUID | None = None, utility_type_id: UUID | None = None):
    return list_records(db, ServiceAccount, query, (ServiceAccount.supply_id,), node_id=node_id, provider_id=provider_id, utility_type_id=utility_type_id)


@router.get("/service-accounts/{record_id}", response_model=ServiceAccountResponse, dependencies=READ)
def get_service_accounts(record_id: UUID, db: Db):
    return get_record(db, ServiceAccount, record_id)


@router.post("/service-accounts", response_model=ServiceAccountResponse, status_code=201, dependencies=WRITE)
def create_service_accounts(data: ServiceAccountCreate, db: Db):
    return save_record(db, ServiceAccount(), data.model_dump())


@router.patch("/service-accounts/{record_id}", response_model=ServiceAccountResponse, dependencies=WRITE)
def update_service_accounts(record_id: UUID, data: ServiceAccountUpdate, db: Db):
    return save_record(db, get_record(db, ServiceAccount, record_id), data.model_dump(exclude_unset=True))
