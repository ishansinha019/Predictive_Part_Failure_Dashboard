# Handoff: Open Verifications and Cautions

**Last updated**: 2026-11-25 (after Milestone 2, before Milestone 3)

Use this file to resume work on another machine, such as a laptop with Docker.
[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) is the authoritative
milestone status; this file lists what still needs verification, what to watch
out for, and how to continue.

## Prompt for the coding agent

> Read `docs/HANDOFF.md` and `docs/IMPLEMENTATION_ROADMAP.md` first. Do not
> start Milestone 3 feature work until the database baseline (section 3.1) is
> fixed and verified. Back up any existing database before changing it. Run the
> verification steps in section 2 and record results in both files. Keep the
> roadmap updated as work progresses.

## 1. Where things stand

| Area | Status |
| --- | --- |
| Milestone 1 (backend, models, JWT auth, Alembic, probes) | Committed in `dc2660d`. |
| Pre-Milestone 2 fixes (routes require auth, no `create_all` at startup/scripts) | Committed in `3101cb2`. |
| Milestone 2 (validation, chronological splits, tuning, baselines, MLflow, v2 artifact, model card) | Committed in `3101cb2`. |
| Backend tests | 19 passed on Python 3.14.10 (in-memory schema from ORM metadata, not migrations). |
| ML tests | 4 passed on Python 3.14.10. |
| Frontend build | `npm ci` and `npm run build` passed. |
| Frontend lint | **Fails** (see 3.4). |
| Fresh `alembic upgrade head` | **Fails** with `NoSuchTableError: prediction_logs`. |
| Docker / PostgreSQL | **Not verified** — Docker engine cannot run on the work PC. |
| Milestone 3 | **Not started.** |

## 2. Verify on the Docker laptop

Run these in order and record results in the roadmap's *Current Status* table.

1. **Pull and set up**
   - `git pull`, then create a Python virtual environment per component.
   - `pip install -r backend/requirements.txt` and `pip install -r ml_model/requirements.txt`.
   - Note the Python version; the work PC used 3.14.10. Dependencies are not
     locked, so versions may differ.
2. **Tests**
   - From `backend`: `python -m pytest`
   - From `ml_model`: `python -m pytest tests`
   - From `frontend`: `npm ci` then `npm run build`
3. **ML artifacts** (Git-ignored, so regenerate them)
   - From `ml_model`: `python -m src.train`
   - Confirm `ml_model/outputs/v2.0/` contains the model, metrics, confusion
     matrices, feature importance, and `MODEL_CARD.md`, and that
     `ml_model/mlflow.db` was created.
   - Optional: `mlflow ui --backend-store-uri sqlite:///mlflow.db` from `ml_model`.
4. **Fresh migration** (expected to fail until 3.1 is fixed)
   - Use a throwaway database, then run `alembic upgrade head` from `backend`.
5. **PostgreSQL in Docker**
   - Example: `docker run --rm -d --name ppfd-pg -e POSTGRES_PASSWORD=<local-only> -p 5432:5432 postgres:16`
   - Point `DATABASE_URL` in `backend/.env` at it, run `alembic upgrade head`,
     seed data, start the API, and repeat the smoke flow: login, prediction,
     fleet, history, and part statistics.
   - There is no `docker-compose.yml` yet; that is Milestone 5.
6. **Image builds**
   - `docker build -t ppfd-backend ./backend` and `docker build -t ppfd-frontend ./frontend`.
     These Dockerfiles have not been built yet.
7. **v2 serving (optional)**
   - Copy `ml_model/outputs/v2.0/part_failure_model.joblib` to
     `backend/models/v2.0/` and set `MODEL_VERSION=v2.0` in `backend/.env`.
     v1 is the default.

## 3. Known issues to fix (Milestone 3 entry work)

### 3.1 Broken Alembic baseline (blocker)
- [The initial revision](../backend/alembic/versions/d9bb4a8c09be_001_initial_schema.py)
  alters `prediction_logs` instead of creating the schema, so a new database
  cannot be initialized. Startup no longer calls `create_all`.
- Fix: write a correct baseline that creates all tables, and a separate safe
  path for existing databases.
- The existing local SQLite database has an empty `alembic_version` table,
  no foreign keys on `prediction_logs`, and two on `work_orders`.
  **Back it up first.** Test both a fresh upgrade and a data-preserving upgrade
  on copies. Do not blindly `alembic stamp head`.

### 3.2 SQLite foreign keys not enforced
- `PRAGMA foreign_keys` is off in
  [database.py](../backend/app/db/database.py); invalid references are accepted.
- Enable it on connect for SQLite, and add a test proving an invalid reference
  is rejected. PostgreSQL enforces foreign keys by default.
- Backend tests build the schema from ORM metadata, so passing tests do not
  prove migrations or integrity. Add a migration-based test.

### 3.3 Authorization (blocker before work-order actions)
- [Login](../backend/app/api/v1/auth.py) auto-registers unknown users and grants
  admin based on the username (an unknown `supervisor` became admin).
- The admin dependency in [deps.py](../backend/app/api/deps.py) exists but is
  not applied to any route.
- Decide an account-provisioning and role policy, remove auto-registration,
  and apply role checks to sensitive operations. Seed credentials are demo-only.

### 3.4 Frontend lint
- `npm run lint` uses `--ext`, which the flat ESLint config does not support.
  Without it, ESLint reports missing `typescript-eslint`.
- Fix the script and dev dependency before making lint a CI gate.

### 3.5 Milestone 3 gaps
- The [WorkOrder model](../backend/app/models/work_order.py) has no technician
  assignment or prediction link, and no work-order endpoints exist.
- Keep existing frontend API contracts working, or update the frontend with them.

## 4. Cautions

- **Synthetic data**: 300 records. Non-failure service ages are 100–359 days
  and failure ages 450–742 days, so the classes are artificially separable.
  Held-out XGBoost average precision ≈ 0.958 is **not** evidence of real-world
  performance. The model must not be used for maintenance or safety decisions.
- **Target leakage**: `service_type` perfectly reveals the target. v2 excludes it;
  the v1 serving model still uses it.
- **No model registry**: MLflow tracking only; no registry or automated promotion yet.
- **MLflow backend**: uses a SQLite tracking DB (`ml_model/mlflow.db`) because the
  installed MLflow rejects the filesystem backend by default.
- **Version drift**: loading the legacy v1 model logs version-compatibility
  warnings. Pin dependencies before CI or containers.
- **Artifacts and DBs are Git-ignored**: `mlflow.db`, `ml_model/outputs/`, and
  local SQLite files must be regenerated or copied separately.
- **Trusted artifacts only**: joblib files can execute code when loaded.
- **Secrets**: keep `.env` values, database passwords, and JWT secrets out of Git.
- **Policy**: only move code or data between machines in ways your
  organization permits. Generated files here are synthetic.

## 5. After verification

Update this file and the roadmap with: machine/OS, Python, Docker and
PostgreSQL versions, each command run, and pass/fail results. Then fix 3.1–3.3
before implementing the Milestone 3 work-order lifecycle.
