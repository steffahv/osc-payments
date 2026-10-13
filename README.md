# WEB-PAYM

Local foundation for a modular administrative payment management platform.
The system does not execute bank transfers.

## Delivery status

Phase A is approved. This delivery implements **Phase B**: repository setup,
frontend, backend, PostgreSQL, Docker Compose, Alembic, and infrastructure checks.
Authentication, RBAC entities, and administration belong to Phases C/D.
The current page is a public welcome screen without business data.

## Project language

All webpage content, documentation, comments, application messages, and new
project material must be written in English. Keep technical and business
terminology consistent across the UI, API, and documentation.

## Quick start on Windows

Requirements: Git and Docker Desktop running Linux containers. Running the
applications outside Docker also requires Python 3.12 and Node.js 24.

Open Docker Desktop, wait for it to be ready, then run from the `paym` root:

```powershell
# Bypass applies only to this process; it does not change the machine policy.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
docker compose up --build -d --wait
docker compose exec backend alembic upgrade head
docker compose ps
```

The setup script preserves an existing `.env`. For a new installation, it
generates a random password without displaying it. Do not share `.env`.
This starts the application on your computer; it does not publish it online.

- Application: http://localhost:5173
- Local Swagger UI: http://localhost:8000/api/docs
- API liveness: http://localhost:8000/api/v1/health/live
- API and PostgreSQL readiness: http://localhost:8000/api/v1/health/ready
- API through the frontend proxy: http://localhost:5173/api/v1/health/ready
- Local PostgreSQL: `127.0.0.1:55432`; inside Docker: `postgres:5432`.

Published ports bind to `127.0.0.1`. If occupied, change `FRONTEND_PORT`,
`BACKEND_PORT`, or `POSTGRES_PORT` in `.env`. When running the backend outside
Docker, also adjust `API_PROXY_TARGET` to the selected backend port.

## Install dependencies locally

Backend, from `backend`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install --require-hashes -r requirements-dev.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Frontend, in another terminal from `frontend`:

```powershell
npm.cmd ci
npm.cmd run dev
```

For this mode, start only PostgreSQL with `docker compose up -d postgres` from
the repository root. Do not run local applications and containers on the same
ports simultaneously. Virtual environment activation is not required.

## Automatic updates during development

Compose mounts `frontend/src`, `index.html`, `vite.config.ts`, and `tsconfig.json`
into the frontend container. Vite uses `server.watch.usePolling` with a 300 ms
interval because Windows file events may not reach Docker's Linux environment.
Saving a React component should update the browser without a container restart.

After pulling changes to these Compose mounts, recreate the frontend once:

```powershell
docker compose up -d --no-deps --force-recreate frontend
```

Run this with the backend already running. `docker compose restart` does not
apply new mounts. No image rebuild is needed for mounted source/configuration
edits. Dependency or Dockerfile changes still require rebuilding the image:

```powershell
docker compose up -d --build --no-deps frontend
```

If updates still fail, inspect `docker compose logs --tail 50 frontend` and
confirm that the component saved in your editor is the one being served.

## Migrations

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic check
```

Phase B has no business schema revisions: it verifies the Alembic environment
and connection. `upgrade head` prepares its tracking table; it does not create
users or roles. Initial domain migrations will accompany the Phase C models.
The application does not call `create_all()` on startup.

## Tests and builds

```powershell
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest
docker compose exec frontend npm run build
```

Local alternative:

```powershell
# From backend; integration is skipped unless RUN_DB_TESTS=1.
.venv/Scripts/python.exe -m pytest
# From frontend.
npm.cmd run build
```

Current tests cover infrastructure and configuration, not authentication.
Recorded results are in [Validation](docs/validation.md).

## Initial administrator

The bootstrap command is not implemented yet; it belongs to Phase C. There is
no default account, password, or public registration endpoint. The future command
will accept email and password through secure input and create explicit grants.

## Stopping and troubleshooting

```powershell
docker compose logs --tail 100 backend
docker compose stop
# Alternatively, remove containers while preserving the PostgreSQL volume:
docker compose down
```

Do not add `-v` to `down` unless you intend to delete the data volume. Changing
`.env` does not change the password of an initialized database; coordinate the
password update within PostgreSQL as well.

## Documentation

- [Technical guide](docs/technical.md): architecture, configuration, maintenance.
- [Business guide](docs/business.md): objectives, concepts, examples, open decisions.
- [Database design](docs/database-design.md): data dictionary and ER diagram.
- [Authorization](docs/authorization.md): views, actions, and contextual scope.
- [Validation](docs/validation.md): evidence and limitations.

Behavior changes must update both technical and business documentation where
applicable. Code comments explain decisions, boundaries, and responsibilities
without mechanically repeating each instruction.
