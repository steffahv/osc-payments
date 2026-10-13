# Phase B validation

Date: 2026-10-13. Original Phase B verification on Windows and Linux containers.
The results below describe that verification, not a new deployment.

## Original results

| Check | Result |
| --- | --- |
| Local Git | Initialized on `main`, no remote or initial commit at handoff |
| `docker compose config --quiet` | Valid configuration |
| Image builds | Frontend and backend built successfully |
| `docker compose up -d --wait` | Three healthy services |
| `alembic upgrade head` | Successful against PostgreSQL |
| `alembic check` | No new upgrade operations detected |
| Windows tests | 6 passed, 1 integration test intentionally skipped |
| Linux tests with `RUN_DB_TESTS=1` | 7 passed, no warnings |
| Windows frontend build | TypeScript and Vite successful |
| Linux frontend build | TypeScript and Vite successful |
| `pip check` | No declared dependency conflicts |
| npm installation audit | 0 vulnerabilities reported on that date |
| Backend locks | 30 runtime packages consistent across both locks |
| Documentation links | Local references checked |
| Git exclusions | `.env`, `.venv`, `node_modules`, `dist`, and `.cache` ignored |

Observed HTTP responses during that verification:

```text
http://127.0.0.1:5173/                         -> 200
http://127.0.0.1:5173/api/v1/health/ready       -> 200
http://127.0.0.1:8000/api/v1/health/live        -> 200
http://127.0.0.1:8000/api/docs                 -> 200
```

## Adjustments made during verification

- Another project occupied port 5432. WEB-PAYM publishes PostgreSQL on
  `127.0.0.1:55432`, keeping `postgres:5432` inside Compose. The other project's
  services were not changed or stopped.
- Downloads and some tools required execution outside the restricted
  environment. Commands were retried with execution approval.
- HTTP tests use `httpx.ASGITransport` to avoid Starlette's deprecated adapter.
  Pytest caching is disabled so container tests do not need write access to `/app`.

## Original handoff state

Test containers were stopped, preserving images and the PostgreSQL volume.
To start them from the repository root: `docker compose up -d --wait`.
The local `.env` contains a generated random password excluded from version control.

## Limitations

HTTP responses and compilation were checked; no automated visual browser
inspection was performed because browser tools were unavailable. The welcome
page does not process protected information.

These checks do not validate login or RBAC, which are not implemented yet.
No production deployment was performed. Domain tables are designed, not migrated.
No operational accounts, roles, or permissions exist; administrator bootstrap
belongs to Phase C.

## English content update

Webpage text, HTML language metadata, documentation, diagrams, code comments,
application errors, and setup messages have been translated into English.
Local verification results:

- Backend: 6 tests passed; 1 PostgreSQL integration test intentionally skipped.
- Frontend: `npm.cmd run typecheck` passed.
- Frontend: `npm.cmd run build -- --configLoader runner` passed. The runner
  loads Vite configuration without the default configuration bundling step.
- Documentation links resolved; a source scan found no remaining Spanish text.
- Local `.env` comments were translated without changing any configuration values.

No containers or application servers were started, and nothing was deployed
as part of this language update. The earlier Linux and HTTP results above
remain historical Phase B verification, not new checks of this update.
