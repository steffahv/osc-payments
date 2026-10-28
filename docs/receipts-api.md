# Stage 4.2: Receipt Management APIs

| Endpoint | Permission | Result |
| --- | --- | --- |
| POST /api/v1/receipts | receipts.create | 201, created receipt |
| GET /api/v1/receipts | receipts.view | 200, paginated receipts |
| GET /api/v1/receipts/{id} | receipts.view | 200, receipt |
| PATCH /api/v1/receipts/{id} | receipts.update | 200, updated receipt |

Permissions are independent and require active global assignments. Team-only
grants do not authorize access; no team filtering or administrator bypass exists.
Cookie sessions and Origin protection are unchanged. No DELETE endpoint exists.

## Input and response

Minimal draft: `{"service_account_id": "<existing UUID>"}`.
Optional fields: receipt_number, period_start, period_end, issue_date, due_date,
amount, currency_code, and electricity_details.

```json
{
  "service_account_id": "<existing electricity account UUID>",
  "receipt_number": "R-001",
  "amount": "123.45",
  "electricity_details": {"consumption_kwh": "456.789"}
}
```

Status defaults to draft, CRM status to pending, currency to PEN.
Clients cannot supply status, status_crm, created_by, IDs, or timestamps.
created_by comes from the authenticated creator and remains unchanged on PATCH.
Responses include statuses, attribution, timestamps, and electricity_details
(null when absent). Decimal values are serialized as strings.

PATCH changes only supplied fields. Nullable receipt fields accept null; required
service_account_id and currency_code do not. Missing electricity_details preserves
the existing row; an object creates/updates it, including an empty object for an
incomplete draft. Use `{"electricity_details":{"consumption_kwh":null}}` to clear
consumption. Explicit `electricity_details:null` is rejected; detail deletion is
not implemented.

Amount accepts up to 16 integer and 2 fractional digits; consumption up to 11
integer and 3 fractional digits. Excess precision, overflow and non-finite values
return 422 instead of silently rounding. Send decimal strings to avoid client
floating-point precision loss. Currency is a three-character string; no currency
catalog or speculative amount-sign restriction is introduced.

Billing periods use dates. POST and merged PATCH state require end >= start when
both exist. Account references must exist; no active-account requirement is added.
Electricity details require an electricity account, including when changing the
account of a receipt with existing details. Receipt and detail changes share one
transaction; updates lock the receipt row while validating merged state.
No uniqueness rules, history events, or workflow transitions are added.

## Lists and errors

Lists use `items`, `total`, `offset`, `limit`, with stable UUID ordering.
Offset defaults to 0; limit defaults to 50 and accepts 1–100.
Optional filters: service_account_id, status, status_crm, and q (literal,
case-insensitive receipt-number substring). Each item includes electricity details.

Errors follow Stage 4.1: detail envelope, 401 unauthenticated, 403 unauthorized or
untrusted Origin, 404 missing receipt, 422 invalid input/reference/merged dates or
utility mismatch, 409 database integrity conflict. Failed writes roll back both
receipt and detail changes.

## Explicit development access

No live user was granted permissions during implementation. With existing
containers running, preview a grant from the paym directory:

```powershell
docker compose exec -T backend python -m app.cli.grant_dev_permissions --email USER_EMAIL --role-code dev_receipt_editor --permission receipts.view --permission receipts.create --permission receipts.update
```

Replace USER_EMAIL with the designated existing active account's email. Review
the returned plan, then repeat the same command with `--apply` to persist it.
Repeat `--permission` for any other explicitly intended existing permission.
The command requires APP_ENV=development, does not create users/catalog entries,
and does not accept passwords. Never change a production environment setting
to use this command.

It creates the specified role only if absent; an existing role must be active
and contain exactly the requested permission set. It never expands/reactivates
an existing role or alters other assignments. Repeated application is idempotent.
Grants are ordinary explicit global assignments, with no authentication bypass.
Catalog entries for disabled modules are rejected. Permissions take effect on
the next request; no login reset is required.

## Verification

```powershell
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest tests/test_receipts_api.py tests/test_dev_permission_command.py -q
docker compose exec -T backend alembic check
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest -q
```

Focused tests cover nullable drafts, decimal precision, partial updates, attribution,
read-only statuses, filters, global RBAC, team-grant denial, Origin checks, forced
transaction rollback, and explicit development grants in isolated schemas.
No schema migration or new permissions are required.

Verified: 26 receipt API tests and 11 grant-command tests passed; full backend
suite 149 passed with the existing Starlette/httpx warning. Alembic reported no
schema drift. The running unauthenticated receipts endpoint returned 401, and
the CLI help entry point was exercised without granting live access.

Stage 4.3 workflow transitions and all frontend, file, dashboard, report, CRM,
and payment-processing work remain outside this stage.
