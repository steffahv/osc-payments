# Database Stage 2: Receipts

Source: [database_architecture_v2.md](database_architecture_v2.md), whose heading
identifies proposal v1, plus the approved Stage 2 schema and business rules.

## Implemented

- `receipts`: existing UUID/timestamp mixins; required service account; nullable
  receipt number, billing dates, issue/due dates, amount, and creator.
- `electricity_receipt_details`: optional one-to-one extension, using
  `receipt_id` as both primary and foreign key; nullable consumption.
- Amount is `NUMERIC(18,2)`; consumption is `NUMERIC(14,3)`, represented by
  Python Decimal. PostgreSQL rounds excess fractional digits to the declared scale
  and rejects values exceeding the available integer precision.
- Currency is non-null `CHAR(3)`, default `PEN`. Non-null status strings default
  to `draft` and `pending`, respectively. Defaults exist in both ORM and database.
- Dates are DATE. The period CHECK rejects an end before the start while allowing
  either date to be missing. Receipt numbers and periods have no UNIQUE constraint.
- All foreign keys use RESTRICT. Receipt service-account and creator fields are
  indexed; the detail primary key already indexes its receipt reference.

## Migration and verification

Revision `c2d8a9410e73` follows `b7e1c4a90261` and creates only these two tables.
It was applied to the local development database and confirmed as the current head.
No seed data is needed. Downgrade removes the two tables and their receipt data;
it was tested only in isolated schemas, never against the application schema.

From `paym`:

```powershell
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest tests/test_receipts.py -q
docker compose exec -T backend alembic check
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest -q
```

Results: 21 focused tests passed; full backend suite **56 passed**, with one
existing Starlette/httpx deprecation warning. Alembic detected no schema drift.
Tests run real migrations in temporary PostgreSQL schemas and roll back all
test DDL/data. They cover defaults, nullable drafts, relationships, delete
restrictions, period ordering, numeric precision/overflow, duplicate records,
independent statuses, schema parity, and upgrade/downgrade.

## Deferred decisions and boundaries

`status` and `status_crm` remain independent unrestricted strings; proposed
values are not database ENUMs or CHECK lists. The business meaning of `paid`
as the final overall state is documented, not enforced as a workflow transition.
Final status vocabularies, transitions, completeness rules, and duplicate policies
remain for later approval. The architecture assigns electricity-only detail
validation to future application logic; no cross-table trigger was introduced.

No APIs, UI, payment execution, CRM integration, permissions, or Stage 3 tables
were added. Existing authentication/RBAC behavior and Stage 1 files were preserved
apart from adding the receipt model imports to the shared metadata registry.
