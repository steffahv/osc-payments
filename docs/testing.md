# Test map and execution guide

## Phase C.3 frontend authentication

From `frontend`, run `node --test tests/api.test.mjs` for the six transport
tests, and `npm.cmd run build` for TypeScript validation and the production build.

Browser checks use installed Edge and the running frontend, without new dependencies:

```powershell
$env:RUN_BROWSER_TESTS = "1"
node --test tests/browser.test.mjs
```

The default browser test mocks authentication responses. It checks protected
navigation, invalid login, successful login, restoration after reload, logout
failure/retry, expired sessions, server failure/retry, and absence of localStorage
data. Set `REAL_BACKEND=1` as a process environment variable to check initial
anonymous access and invalid credentials against FastAPI; successful sessions
still use fixtures. No database users are created.

Verification: six transport tests and the mocked browser flow passed.
After the backend restart, all three containers were healthy and the browser
test with `REAL_BACKEND=1` passed: anonymous access and invalid credentials were
checked against the live API. Successful sessions still used mocked responses.
A successful login using a real account remains a manual check:
sign in at `http://localhost:5173/login`, reload, sign out, and confirm direct
navigation to `/` redirects to login. The existing 19 backend tests passed during
C.2 restoration; they were not rerun for these frontend-only changes.

Route guards enforce navigation only. Backend RBAC remains a separate requirement.
The sections below retain the earlier test map and historical phase results.

## Scope and status

This document maps requirements to checks and explains how to run them.
[Validation](validation.md) records historical execution results; it is not the
test inventory. Update both documents when coverage or verified behavior changes.

Current phase: B. There are seven backend tests: six checks that do not require
a database and one optional PostgreSQL integration test. Authentication and RBAC
are designed but not implemented or tested yet. No frontend component or browser
automation suite exists. A successful build does not prove UI behavior or access control.

## Implemented automated tests

Paths below are relative to `backend/tests`. Test IDs are documentation references,
not pytest markers.

| ID | Requirement / behavior | Source and test function | Level / dependencies | Assertions and limits |
| --- | --- | --- | --- | --- |
| CFG-01 | Preserve special characters in database credentials without displaying the password | `test_config.py::test_database_url_preserves_special_password_characters` | Unit; no database | URL retains the supplied password; normal URL string representation hides it. Does not audit every log path. |
| CFG-02 | Require secure cookies in production configuration | `test_config.py::test_production_requires_secure_cookies` | Unit; no database | Production configuration rejects `cookie_secure=False`. Does not test real cookie issuance. |
| CFG-03 | Keep idle expiration within absolute session duration | `test_config.py::test_idle_timeout_cannot_exceed_absolute_timeout` | Unit; no database | Configuration rejects an idle timeout greater than the absolute limit. Does not implement expiration. |
| API-01 | Liveness must not depend on database availability | `test_health.py::test_liveness_does_not_require_database` | In-process HTTP; no database | `/api/v1/health/live` returns 200 and `{"status":"ok"}`. |
| API-02 | Readiness must use its database dependency | `test_health.py::test_readiness_checks_database` | In-process HTTP; mocked database session | Returns 200 and calls `execute` once. This test alone does not establish a real database connection. |
| API-03 | Handle database failure without exposing connection details | `test_health.py::test_readiness_failure_does_not_leak_connection_details` | In-process HTTP; simulated SQLAlchemy error | Returns 503 and a generic English message; the injected secret is absent from the response. |
| DB-01 | Connect to the actual PostgreSQL database | `test_database.py::test_postgresql_connection` | Integration; PostgreSQL and `RUN_DB_TESTS=1` | `SELECT 1` returns 1 and `SELECT version()` identifies PostgreSQL. Does not validate domain tables or migrations. |

## Execution commands

### Local checks without a database

From `backend`, with dependencies installed:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected default result: **6 passed, 1 skipped**. `DB-01` is skipped unless
`RUN_DB_TESTS=1`. To explicitly exclude integration tests, even if that variable
is already set:

```powershell
.venv/Scripts/python.exe -m pytest -m "not integration"
```

Expected result: **6 passed, 1 deselected**.

`conftest.py` supplies fallback test environment values using `setdefault`.
Existing process values take precedence. In particular, its placeholder password
overrides `.env` loading if no password was already supplied through the process
environment. For real database tests, use the Compose command below, which passes
the actual connection settings to the container. Do not paste secrets into commands.

### Full current suite with PostgreSQL

From `paym`, with the backend and PostgreSQL containers already running:

```powershell
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest
```

Expected result: **7 passed**. The environment override applies to this test
process. This command does not start or recreate containers. See the
[README](../README.md) for startup instructions.

For only the PostgreSQL test:

```powershell
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -m integration
```

Expected result: **1 passed, 6 deselected**. The current database test only reads
data. Future authentication/RBAC tests that create records must use a dedicated
test database and isolated fixtures, never production data.

### Discover or run a specific test

From `backend`:

```powershell
.venv/Scripts/python.exe -m pytest --collect-only -q
.venv/Scripts/python.exe -m pytest tests/test_health.py::test_readiness_failure_does_not_leak_connection_details -v
```

## Build, schema, and manual checks

These supplement automated tests; they are not additional pytest cases.

| ID | Check | Command or procedure | Expected result |
| --- | --- | --- | --- |
| BUILD-01 | TypeScript validation | From `frontend`: `npm.cmd run typecheck` | Exit code 0 |
| BUILD-02 | Frontend production bundle | From `frontend`: `npm.cmd run build` | TypeScript and Vite succeed |
| BUILD-03 | Frontend build in Linux | From `paym`: `docker compose exec frontend npm run build` | Build succeeds in the existing container |
| SCHEMA-01 | Alembic consistency | From `paym`: `docker compose exec backend alembic check` | No new upgrade operations detected; Phase B has no domain revisions |
| MAN-01 | Service health | `docker compose ps` | Three running, healthy services |
| MAN-02 | English welcome page | Open `http://localhost:5173` | Heading, descriptions, cards, and footer render in English |
| MAN-03 | Live source updates | Save a temporary text edit in `welcome-page.tsx`, observe the browser, then restore the edit | Page updates without restarting containers |
| MAN-04 | API via frontend proxy | Open `http://localhost:5173/api/v1/health/ready` | HTTP 200 and `{"status":"ok"}` |
| MAN-05 | API documentation | Open `http://localhost:8000/api/docs` | Health routes appear in local Swagger UI |
| MAN-06 | Unknown frontend route | Open `http://localhost:5173/nonexistent-page` | English “Page not found” view with a working home link |

## Planned coverage: Phase C and later

All rows below are **planned, not implemented**. Names such as analytics and
receipts remain illustrative; use controlled test fixtures until the actual
modules are defined. None of these cases requires implementing payment workflows.

| ID | Requirement | Scenario / expected behavior | Planned test boundary |
| --- | --- | --- | --- |
| AUTH-01 | Valid login | Correct credentials create a session; response exposes no password hash or raw stored secrets | API + PostgreSQL |
| AUTH-02 | Invalid login | Wrong password and unknown account receive generic failures; failures are audited | API + PostgreSQL |
| AUTH-03 | Inactive user | Login denied; previously issued sessions cannot access protected endpoints | API + PostgreSQL |
| AUTH-04 | Authentication required | Missing, invalid, expired, or revoked session results in 401 | API + PostgreSQL |
| AUTH-05 | Logout and revocation | Logout revokes the session; replaying its cookie fails | API + PostgreSQL |
| AUTH-06 | Session lifetime | Absolute and idle expiration enforced using controlled time | Service + API |
| AUTH-07 | CSRF and cookies | Unsafe requests reject missing/invalid CSRF or origin; cookie attributes match the environment | API |
| AUTH-08 | Login rate limits | Account and IP limits work across requests and cannot lose concurrent increments | API + PostgreSQL |
| RBAC-01 | Backend view protection | Authenticated user without required view permission receives 403, including direct API access | API + PostgreSQL |
| RBAC-02 | Authorized role | An active assignment and matching `role_permissions` entry grant the requested action | Service + API |
| RBAC-03 | Team isolation | A team A assignment does not authorize team B data; collection and individual-resource queries enforce scope | API + PostgreSQL |
| RBAC-04 | Membership is not a grant | Active `team_memberships` without a role assignment grants no access | Service + API |
| RBAC-05 | Role assignment and revocation | Add/revoke assignments; effective access changes on the next request without another login | API + PostgreSQL |
| RBAC-06 | Role permission changes | Adding/removing `role_permissions` affects all applicable assignments; grants from other roles remain effective | Service + API |
| RBAC-07 | Global and team union | Combine scopes correctly; removing a team grant does not cancel a surviving global grant | Service + API |
| RBAC-08 | Disabled entities | Inactive roles/teams/memberships and disabled modules do not grant the corresponding access | Service + API |
| RBAC-09 | Membership removal | Deactivate membership and revoke contextual assignments atomically; reactivation does not restore revoked roles | API + PostgreSQL |
| RBAC-10 | Administrative protection | Team-scoped permissions cannot manage the global identity/role catalog | API + PostgreSQL |
| DATA-01 | Relationship uniqueness | Duplicate membership and role-permission pairs fail; duplicate active assignments fail; revoked assignment history remains | PostgreSQL constraints |
| DATA-02 | Context integrity | Global assignment requires NULL team; team assignment requires a matching membership and valid foreign keys | PostgreSQL constraints + service |
| DATA-03 | Concurrent membership changes | Assignment creation and membership removal serialize consistently, leaving no effective invalid grant | PostgreSQL transactions |
| AUDIT-01 | Sensitive action history | Login, logout, user deactivation, role/permission changes, and membership changes record expected actor/action/result without secrets | API + PostgreSQL |
| UI-01 | Protected navigation | Unauthenticated access redirects to login; menu/actions reflect effective permissions; distinguish 401 and 403 | Frontend/browser tests |

Migration upgrade tests and isolated database fixtures must accompany the first
domain migration. Analytics aggregates and receipt downloads need scope tests
when those features are implemented, not just tests that hide menu entries.

## Maintaining this map

When adding a behavior, add or update its requirement row, link the actual test
function once implemented, and record execution evidence in `validation.md`.
Do not mark planned cases as passing. Record skipped tests and their reasons,
and distinguish manual checks, compilation, and automated assertions. No coverage
percentage is currently measured.
