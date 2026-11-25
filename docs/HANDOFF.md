# Handoff: Open Verifications and Cautions

**Last updated**: 2026-11-25 (after the Milestone 3 backend work)

Use this file to resume work on another machine, such as a laptop with Docker.
[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) is the authoritative
milestone status; this file lists what still needs verification, what to watch
out for, and how to continue.

## Prompt for the coding agent

> Read `docs/HANDOFF.md`, `docs/IMPLEMENTATION_ROADMAP.md` and
> `backend/alembic/README` first. Milestone 3 (backend) was verified only on
> SQLite. Run the verification steps in section 2 on this machine, fix whatever
> fails on PostgreSQL or Docker, and record results in both files. Back up any
> existing database before migrating it. Keep the roadmap updated.

## 1. Where things stand

| Area | Status |
| --- | --- |
| Milestone 1 (backend, models, JWT auth, Alembic, probes) | Committed in `dc2660d`; its gaps were fixed in Milestone 3. |
| Milestone 2 (ML pipeline, MLflow, v2 artifact, model card) | Committed in `3101cb2`. |
| Milestone 3 (repositories, services, work orders, roles, migrations, tests) | Implemented; **check `git log` for whether it has been committed**. 60 backend tests pass on Python 3.14.10 with SQLite. |
| PostgreSQL | **Not verified** (DDL and queries were only compiled with the PostgreSQL dialect). |
| Docker images / compose | **Not verified**; no `docker-compose.yml` yet (Milestone 5). |
| Frontend | Builds; lint is broken; no work-order UI (Milestone 4). |

## 2. Verify on the Docker laptop

Record results in the roadmap's *Current Status* table.

1. **Set up**: `git pull`; create a Python virtual environment;
   `pip install -r backend/requirements.txt` and `pip install -r ml_model/requirements.txt`.
   Note the Python version (the work PC used 3.14.10; dependencies are not pinned).
2. **Backend tests (SQLite)**: from `backend`, with `DATABASE_URL=sqlite:///:memory:` and
   any `SECRET_KEY` set in the environment: `python -m pytest`. Expect 60 passed.
3. **ML tests and artifacts** (Git-ignored, so regenerate): from `ml_model`,
   `python -m src.train` and `python -m pytest tests`.
4. **PostgreSQL** (the important new check):
   - `docker run --rm -d --name ppfd-pg -e POSTGRES_PASSWORD=<local-only> -e POSTGRES_DB=ppfd -p 5432:5432 postgres:16`
   - In `backend/.env` set `DATABASE_URL=postgresql+psycopg2://postgres:<local-only>@localhost:5432/ppfd` and a `SECRET_KEY`.
   - From `backend`: `alembic upgrade head`, `python seed_db.py`, then
     `alembic downgrade base` and `alembic upgrade head` again.
   - Start the API (`uvicorn app.main:app`) and repeat the smoke flow: login as
     `admin`/`admin123`, `technician`/`tech123`, `operator`/`operator123`
     (demo-only passwords); list machines; predict; create a work order from the
     returned `prediction_id` (needs a risk above 0.5, e.g. `M-185`/`P-BRG-02`
     with 700 days, after cancelling the seeded sample order); change its status
     to `In_Progress` then `Completed`.
   - To run the test suite against PostgreSQL, point `tests/conftest.py` at it
     temporarily; the tests currently use in-memory SQLite.
   - Things most likely to differ from SQLite: the partial unique index
     `uq_work_orders_active_machine_part`, `ILIKE` search with escaping,
     `NULLS LAST` ordering, and the batch-mode migrations.
5. **Image builds**: `docker build -t ppfd-backend ./backend` and
   `docker build -t ppfd-frontend ./frontend` (never built yet).
6. **Frontend**: `npm ci`, `npm run build`, then log in through the UI against
   the running API and check the fleet page (it requests `limit=500`).
7. **v2 serving (optional)**: copy `ml_model/outputs/v2.0/part_failure_model.joblib`
   to `backend/models/v2.0/` and set `MODEL_VERSION=v2.0`. v2 predictions are
   *experimental*: the API will refuse to create work orders from them.

## 3. If you bring the old local SQLite database over

It was created before Alembic and holds 524 prediction logs, 106 machines,
3 users, 6 parts and 1 work order. **Back it up first.**
`alembic upgrade head` refuses to run because 64 logs reference unregistered
machines. On a copy, `alembic -x repair_orphans=true upgrade head` registered
55 machines (type taken from the ID prefix), kept every log, and passed
`PRAGMA foreign_key_check`. Decide whether those machines should instead be
reviewed or deleted. Never `alembic stamp head` on it. The database file is not
in Git, so it must be copied separately (only if your organization permits).

## 4. Known gaps

- **PostgreSQL / Docker unverified** (section 2).
- **Frontend**: `npm run lint` fails (`--ext` is unsupported by the flat ESLint
  config; `typescript-eslint` missing). No UI for work orders or user admin.
- **Security**: no refresh tokens, password change/reset, user deactivation or
  rate limiting. Accounts exist only via the seed script or an admin calling
  `POST /api/v1/auth/users`. Seeded passwords are demo-only. Keep `.env`
  values, database passwords and JWT secrets out of Git.
- **Behaviour changes to remember**: viewers cannot predict; `daily-scan` is
  admin-only; unknown machine/part IDs return 404; work orders need an
  existing machine and part; one active work order per machine and part.
- **Work orders**: `estimated_cost` defaults to the part's unit cost (no labour
  rate); concurrent edits are not versioned.
- **Dependencies** are unpinned; loading the legacy v1 model logs
  scikit-learn/XGBoost version warnings.
- **Older models** still use `datetime.utcnow()` (deprecation warnings).

## 5. Cautions

- **Synthetic data**: 300 records with artificially separable classes
  (non-failure ages 100-359 days, failures 450-742). The held-out XGBoost
  average precision of about 0.958 is **not** evidence of real-world
  performance. Do not use the model for maintenance or safety decisions.
- **Target leakage**: `service_type` perfectly reveals the target. v2 excludes
  it; the default v1 model still uses it.
- **No model registry**: MLflow tracking only (`ml_model/mlflow.db`, SQLite);
  no registry or automated promotion.
- **Git-ignored files** (`mlflow.db`, `ml_model/outputs/`, local SQLite files,
  `backend/.env`) must be regenerated or copied separately.
- **Trusted artifacts only**: joblib files can execute code when loaded.
- **Policy**: only move code or data between machines in ways your
  organization permits. The data in this project is synthetic.

## 6. After verification

Update this file and the roadmap with machine/OS, Python, Docker and PostgreSQL
versions, each command run, and pass/fail results. Then continue with
Milestone 4 (frontend) using the work-order endpoints documented at `/docs`.
