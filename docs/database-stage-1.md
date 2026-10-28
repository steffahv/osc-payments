# Database Stage 1

Implemented against [database_architecture_v2.md](database_architecture_v2.md)
(its heading identifies proposal v1), with the user's Stage 1 approval and
clarifications taking precedence over its earlier review-only status.

## Schema

- Tables: `utility_types`, `node_types`, `nodes`, `providers`, `service_accounts`.
- All use the existing UUID identity and UTC timestamp mixins, plus `is_active`.
- Catalog codes are unique. Node codes and provider tax IDs are not constrained
  to be unique until actual data confirms those rules.
- Nodes require a node type. Service accounts require a node, provider, utility
  type, and text `supply_id`; leading zeros are preserved.
- Multiple accounts per node are allowed. No UNIQUE constraint covers supply IDs,
  alone or in combination, pending actual-data review.
- Foreign keys use RESTRICT; deactivate masters instead of deleting them.
- Foreign keys, node codes, and supply IDs have non-unique indexes.
- Provider tax ID and region are optional. No region catalog is introduced.

## Migration and catalogs

`b7e1c4a90261` follows `ced18c17b404`. It adds only these five tables and seeds:

| Catalog | Code | Name |
| --- | --- | --- |
| Utility type | electricity | Electricity |
| Node type | TX | Transport |
| Node type | AX | Access |
| Node type | MC | Definition pending |

No seed framework existed. Seeds therefore live in the migration, use fixed UUIDs
and PostgreSQL `ON CONFLICT (code) DO NOTHING`, and preserve existing labels and
activation flags. Electricity is the only seeded utility; future utilities are
not implemented. No providers, nodes, or service accounts are seeded.

The downgrade removes the five Stage 1 tables and their data; it is intended only
for deliberate rollback. It was tested solely inside an isolated temporary schema.
No downgrade was run against the application's schema.

## Verification

From `paym`, with the existing containers running:

```powershell
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest tests/test_master_data.py -q
docker compose exec -T backend alembic check
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest -q
```

Results: 15 focused PostgreSQL tests passed; full backend suite 35 passed,
with the existing Starlette/httpx deprecation warning. Migration applied to the
local development database; Alembic reports no new upgrade operations.

Focused tests apply the migration in unique temporary schemas and roll back all
DDL/data afterward. They cover migration/model parity, seed idempotency, defaults,
foreign keys, protected master references, duplicate supply IDs, multiple accounts,
leading zeros, deactivation, and migration downgrade/upgrade.

Pending: actual-data review of uniqueness rules, provider region semantics, and
the business definition of MC. Authentication/RBAC behavior, APIs, frontend,
receipts, documents, and workflows are outside this change. Stage 2 is not started.
