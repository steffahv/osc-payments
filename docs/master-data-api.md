# Stage 4.1: Permission catalog and master-data APIs

## Access model

V1 module access uses explicit global role assignments independently of team
membership. No team-record filtering is implemented. Team-scoped grants alone
cannot authorize these endpoints. Roles are reusable; no role-name checks or
administrator bypass exist. Account creation and team assignment are not part
of this stage.

Reads require `master_data.view`; writes require `master_data.manage`.
These permissions are independent and additive across active global assignments.
Inactive roles, revoked assignments, and disabled modules do not grant access.
Authentication/session and Origin protections are unchanged.

## Catalog

Migration `e4a109bc7283`, following `d39f6b208a14`, registers:

| Module | Permissions |
| --- | --- |
| dashboard | dashboard.view |
| receipts | receipts.view, receipts.create, receipts.update |
| reports | reports.view, reports.export |
| master_data | master_data.view, master_data.manage |
| admin | admin.users_manage, admin.roles_manage |

The approved administration names retain the existing single-dot
`module.action` convention. Registration is idempotent and preserves existing
module IDs, labels, activation flags, and grants. No permissions are assigned to
users or roles, including the development test user. Downgrade deliberately
retains shared catalog data to avoid removing existing or subsequently used grants.
Registering a permission does not implement its module's API or UI.

## Endpoints

Prefix: `/api/v1/master-data`.

| Resource | Methods |
| --- | --- |
| /utility-types | GET list |
| /utility-types/{id} | GET detail |
| /node-types | GET list |
| /node-types/{id} | GET detail |
| /nodes | GET list, POST create |
| /nodes/{id} | GET detail, PATCH update |
| /providers | GET list, POST create |
| /providers/{id} | GET detail, PATCH update |
| /service-accounts | GET list, POST create |
| /service-accounts/{id} | GET detail, PATCH update |

Use PATCH with `{"is_active": false}` or `{"is_active": true}` to deactivate
or reactivate writable masters. No DELETE endpoints exist; catalogs are read-only.

Lists return `{"items": [...], "total": 0, "offset": 0, "limit": 50}`.
Pagination uses stable UUID order; offset must be nonnegative and limit is 1–100.
Optional `is_active` filters records; both active and inactive records appear
when omitted. `q` performs literal case-insensitive substring matching:
catalog code/name, node code/name, provider name/tax ID/region, or supply ID.
Nodes additionally filter by `node_type_id`; service accounts filter by
`node_id`, `provider_id`, and `utility_type_id`.

POST returns 201, GET/PATCH 200. Inputs reject unknown fields, invalid UUIDs,
blank required text and overlong values. PATCH updates only supplied fields;
only provider tax ID and region can explicitly be set to null. Empty PATCH
is accepted as a no-op. References must exist; no additional active-parent
business rule is imposed. Supply IDs remain strings with leading zeros preserved.
Node code/name remain independent; deferred uniqueness rules are unchanged.

Errors retain FastAPI's `detail` envelope: 401 unauthenticated, 403 forbidden
(including untrusted Origin), 404 missing resource, 422 validation or missing
reference, and 409 concurrent integrity conflict. Validation detail may be an
array; other errors use strings. Database exceptions are not exposed.

## Verification

```powershell
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest tests/test_master_data_api.py -q
docker compose exec -T backend alembic check
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest -q
```

Results: 38 focused tests and 112 total backend tests passed, with the existing
Starlette/httpx deprecation warning. No schema drift. Live unauthenticated
master-data access returned 401; database catalog and migration head were verified.
Tests use isolated schemas, real session/RBAC dependencies, and rolled-back data.

No receipt CRUD, dashboard/report APIs, frontend, public registration, account
management, or workflow implementation was added. Viewer receipt exclusion will
require appropriate grants when roles are provisioned and permission checks when
receipt endpoints are implemented. No further stage has been started.
