# Implementation Roadmap: Production Transformation

**Project Name**: Predictive Part Failure Dashboard (PPFD)  
**Execution Strategy**: Milestone-Based Incremental Delivery  
**Document Version**: 2.2

---

## Roadmap Strategy & Principles

1. **Incremental Delivery Without Regression**: Existing user flows (Login, Fleet Overview, Machine Detail, Prediction Form, Charts) will remain functional at every stage.
2. **Interview-Grade Engineering**: Every milestone directly addresses topics probed in technical interviews (system design, REST API best practices, MLOps, containerization, CI/CD, cloud architecture).
3. **Reproducibility**: Every layer must have automated verification and documented local commands.

---

## Current Status (reviewed 2026-11-25, after Milestone 3 backend work)

The Milestone 3 backend (repositories, services, work-order lifecycle, roles,
migrations) is implemented and verified **locally on SQLite only**. It is not
production-ready until PostgreSQL and Docker are verified on an authorized
machine, a work-order UI exists (Milestone 4), and the carried-over cautions in
[HANDOFF.md](./HANDOFF.md) are resolved. Frontend lint is still broken.

Pending verification steps (Docker, PostgreSQL) and cautions for continuing on
another machine are tracked in [HANDOFF.md](./HANDOFF.md).

| Check | Result |
| --- | --- |
| Backend tests | 60 passed on Python 3.14.10 (includes API integration, role, migration and foreign-key tests). |
| ML tests | 4 passed on Python 3.14.10 (not re-run after Milestone 3; ML code was untouched). |
| Fresh database | `alembic upgrade head` now succeeds (SQLite); migrated schema matches the ORM models; downgrade to base works; seed script runs. |
| Existing database | On a **copy** of the real local SQLite DB: refused to upgrade because 64 prediction logs referenced unregistered machines; `alembic -x repair_orphans=true upgrade head` registered 55 machines, kept all 524 logs, and `PRAGMA foreign_key_check`/`integrity_check` were clean. The original file was not modified. |
| Live API smoke test | Real server on a fresh seeded SQLite DB: unknown-user login 401, viewer read-only, technician predict, work-order create/409/list, scan admin-only, OpenAPI tags present. |
| Frontend | `npm run build` passed with the fleet request now passing `limit=500`; `npm run lint` still fails with an unsupported `--ext` option (and missing `typescript-eslint`). No work-order UI yet. |
| PostgreSQL | DDL and repository queries were only **compiled** with the PostgreSQL dialect; no PostgreSQL server was run. Unverified. |
| Docker | Docker engine is unavailable on this workstation; image builds and containers remain unverified. |

## Milestone 1: Backend Architecture, Relational Modeling & Authentication

**Status**: Foundation implemented. The baseline migration, foreign-key
enforcement and authorization gaps were fixed in Milestone 3 (see below);
PostgreSQL is still unverified.

### Objective
Replace the prototype database setup and mock authentication with a secure, normalized, production-grade foundation using SQLAlchemy 2.0, Alembic migrations, PostgreSQL compatibility, and real bcrypt JWT security.

### Affected Files
- `backend/app/db/database.py`
- `backend/app/models/user.py`, `backend/app/models/machine.py`, `backend/app/models/part.py`, `backend/app/models/prediction_log.py`, `backend/app/models/work_order.py`
- `backend/alembic/`, `backend/alembic.ini`
- `backend/app/core/security.py`, `backend/app/core/middleware.py`, `backend/app/core/logging.py`
- `backend/app/api/deps.py`, `backend/app/api/v1/auth.py`
- `backend/seed_db.py`
- `backend/tests/test_auth.py`, `backend/tests/test_models.py`

### Deliverables & Tasks
1. **Database Schema Normalization**:
   - Model `User` (username, password hash, role).
   - Model `Machine` (`id`, `machine_type`, `status`, `install_date`).
   - Model `Part` (`id`, `category`, `name`, `expected_lifespan_days`, `unit_cost`).
   - Model `WorkOrder` (`id`, `machine_id`, `part_id`, `status`, `priority`, `estimated_cost`).
   - Declare foreign keys and composite indexes in `PredictionLog`.
   - **Open**: SQLite connections do not enable foreign-key enforcement. The
     local `backend/sql_app.db` also has no foreign keys on `prediction_logs`,
     and its `alembic_version` table has no revision recorded.
2. **Alembic Migration Setup**:
   - Initialize Alembic environment.
   - Generate initial migration revision `001_initial_schema`.
   - **Blocked**: The revision alters an existing table instead of creating a
     fresh schema. Establish and test a baseline for fresh databases and a
     safe upgrade path for existing data. Back up existing databases before
     migration; do not blindly stamp them as migrated.
3. **Production Authentication & Security**:
   - Real bcrypt hashing and verification in `app/core/security.py`.
   - Dependency `get_current_user` checking JWT signature, expiry, and user existence in DB.
   - Seed default initial users (`admin` / `technician`) with hashed passwords.
   - Data routers require authentication, but role restrictions are not
     applied. Login auto-registers unknown users and can assign an admin role
     based on username; seeded credentials are for demo use only. Define a
     safe account-provisioning and authorization policy before sensitive
     work-order operations.
4. **Middleware & Health Probes**:
   - Add Correlation ID (`X-Correlation-ID`) and request execution timer (`X-Process-Time`) middleware.
   - Add `/healthz` and `/readyz` probes.
5. **Testing**:
   - Pytest suite covering token generation, password hashing, invalid
     credentials, authenticated endpoints, and ORM relationships.
   - **Open**: Add migration and foreign-key enforcement tests. The current
     in-memory test setup bypasses Alembic and does not enforce SQLite foreign keys.

---

## Milestone 2: Machine Learning Engineering Pipeline & Model Registry

**Status**: The experimental training and evaluation pipeline is implemented
and tested locally. Model registry, controlled promotion, and production
validation remain open; the backend still defaults to the legacy v1 model.

### Objective
Transform the ML component from loose scripts into an audited, reproducible MLOps pipeline featuring Pandera data validation, baseline comparisons, MLflow experiment tracking, and automated model card generation.

### Affected Files
- `ml_model/src/validate.py` (New: Pandera schema validation)
- `ml_model/src/preprocess.py` (Refactored: Scikit-learn Pipeline)
- `ml_model/src/train.py` (Refactored: MLflow logging, baselines, and hyperparameter tuning)
- `ml_model/src/evaluate.py` (New: Evaluation report and confusion matrix export)
- `ml_model/tests/test_ml_pipeline.py` (New: Automated ML unit tests)
- `docs/MODEL_CARD.md` (New: Model card documentation)

### Deliverables & Tasks
1. **Data Integrity & Validation**:
   - Implement `validate_dataset()` using Pandera to enforce strict schemas on service records.
2. **Baseline Model Comparison**:
   - Train `DummyClassifier` (chance baseline) and `LogisticRegression` (linear baseline).
   - Evaluate against `XGBClassifier` using average precision (a precision-recall summary), ROC-AUC, Recall (Class 1), and F1-score.
   - Tune XGBoost on a chronological validation split and evaluate on a later held-out split.
3. **MLflow Experiment Tracking**:
   - Log runs, parameters (`scale_pos_weight`, `learning_rate`, `max_depth`), metrics, and feature importances.
4. **Training-Serving Consistency (v2)**:
   - Bundle preprocessor and model into a single unified sklearn Pipeline object.
   - Export versioned artifact with explicit metadata schema.
   - v2 is opt-in: it must be copied into the backend model directory and
     selected with `MODEL_VERSION=v2.0`. The default v1 artifact still uses
     `service_type`, which is excluded from v2 due to outcome leakage.
5. **Testing**:
   - Tests verify chronological split boundaries, deterministic inference,
     handling of unseen categorical values, and training/export.
6. **Remaining registry and reliability work**:
   - MLflow tracks experiments and artifacts, but no model is registered in
     an MLflow Model Registry and there is no automated promotion process.
     Generated v2 outputs and the local MLflow database are Git-ignored and
     must be regenerated or transferred separately on another machine.
   - Dependency versions are recorded in the generated model card but are not
     pinned or locked. Verify reproducibility and serving compatibility before
     promoting a model.
   - The data is synthetic and small: non-failure service ages are 100-359
     days and failure ages are 450-742 days. High scores on this dataset do
     not establish real-world model performance or safety.

---

## Milestone 3: Clean API Services, Repositories & Work Order Lifecycle

**Status**: Backend implemented and verified locally on SQLite (60 backend tests,
live smoke test). Not complete: PostgreSQL/Docker are unverified, the frontend
has no work-order UI yet (Milestone 4), and the review items below remain open.

### Entry Criteria and Carry-Forward Work (all addressed)
1. **Done** - Alembic baseline (`d9bb4a8c09be`) creates a new database; a
   data-preserving upgrade handles pre-Alembic databases (opt-in
   `-x repair_orphans=true` registers machines referenced only by prediction
   logs). SQLite foreign keys are enforced by the app and tested. See
   `backend/alembic/README`. PostgreSQL still needs verification.
2. **Done** - Login no longer auto-registers users or grants admin by name.
   Admins create accounts via `POST /api/v1/auth/users`. Roles: `viewer`
   (read-only), `technician` (predict, create/update work orders, self-assign),
   `admin` (everything, assign any technician, daily scan, user creation).
3. **Done** - Fleet and prediction responses only gained fields. Behaviour
   changes: predicting for an unknown machine or part, and history/part stats
   for unknown IDs, now return 404 (they previously logged orphan rows or
   returned empty data); viewers get 403 on prediction; the simulation
   endpoint is admin-only; simulation recommendations now use the same text as
   predictions. `FleetPage` requests `limit=500`.
4. **Done** - Migration `a3f1c2d4e5b6` adds `assigned_technician_id`,
   `prediction_log_id`, `created_by_id` to work orders, `model_version` to
   prediction logs, and a unique index allowing one active work order per
   machine and part.
5. **Done** - `tests/test_api_v1.py` covers roles, validation, pagination,
   predict -> work order -> history, failures, and experimental-model rules.
   Predictions from versions in `EXPERIMENTAL_MODEL_VERSIONS` (default `v2.0`),
   historical records, and risk at or below 0.5 cannot create work orders.

### Open items after Milestone 3
- Run `alembic upgrade head`, the seed script and the test suite against a real
  PostgreSQL server (the migrations were only tested on SQLite).
- Decide whether the 55 machines auto-registered in the real local database
  (type taken from the ID prefix) need review before relying on fleet data.
- No refresh tokens, password change/reset, user deactivation, or rate limiting.
  Seeded demo passwords must not be used outside local development.
- Work-order `estimated_cost` defaults to the part unit cost (no labour rate is
  modelled). Concurrent updates are not versioned (last write wins).
- `datetime.utcnow()` is still used by older models (deprecation warnings).
- Dependencies are not pinned; frontend lint is still broken.

### Objective
Restructure backend business logic into Repository and Service patterns, upgrade to Pydantic v2 DTOs, and introduce maintenance work order creation to close the business loop on prediction alerts.

### Affected Files
- `backend/app/schemas/` (Typed Pydantic v2 schemas with examples and validation)
- `backend/app/repositories/` (Data access abstractions)
- `backend/app/services/` (Domain services: `MachineService`, `PredictionService`, `WorkOrderService`)
- `backend/app/api/v1/work_orders.py` (New: Work order management)
- `backend/app/api/v1/machines.py` (Refactored: Pagination, sorting, filtering)
- `backend/tests/test_api_v1.py` (New: End-to-end API integration tests)

### Deliverables & Tasks
1. **Repository & Service Layer**:
   - Decouple raw database queries from route handlers.
   - Implement `PredictionService` that orchestrates ML inference, DB logging, and business recommendations.
2. **Work Order Management API**:
   - `POST /api/v1/work-orders`: Creates planned maintenance work order from prediction risk.
   - `GET /api/v1/work-orders`: Lists pending work orders with machine and technician metadata.
3. **API Contracts**:
   - Add pagination parameters (`skip`, `limit`, `search`, `status`) to fleet endpoints.
   - Strong Pydantic v2 validation and OpenAPI Swagger tags.
4. **Testing**:
   - Integration tests testing end-to-end predict -> work order creation -> history update.

---

## Milestone 4: Frontend Modernization (TanStack Query, shadcn/ui & Forms)

**Status**: Planned. The current production build passes, but the lint command
and ESLint configuration/dependencies must be reconciled before lint is used
as a quality gate.

### Objective
Elevate the React frontend to modern industry standards by introducing TanStack Query for server state, shadcn/ui for accessible styling, and React Hook Form + Zod for robust form handling.

### Affected Files
- `frontend/src/app/queryClient.ts`
- `frontend/src/components/ui/` (Button, Card, Badge, Table, Dialog, MetricStat, Skeleton)
- `frontend/src/features/` (Modular hooks: `useFleet`, `useMachine`, `usePredict`, `useWorkOrders`)
- `frontend/src/features/maintenance/WorkOrderModal.tsx`
- `frontend/src/features/predictions/PredictionForm.tsx` (Zod + React Hook Form refactor)
- `frontend/src/features/authentication/LoginForm.tsx` (Zod + React Hook Form refactor)
- `frontend/tests/` (Vitest & React Testing Library suites)

### Deliverables & Tasks
1. **TanStack Query Integration**:
   - Replace all ad-hoc `useEffect` fetches with custom Query and Mutation hooks.
   - Add automatic query caching, background refetching, and query invalidation on mutations.
2. **Design System & shadcn/ui Primitives**:
   - Build a consistent component library with Radix UI accessibility tokens.
   - Replace scattered CSS Modules with unified Tailwind design tokens.
3. **Form Handling with Zod**:
   - Form schemas for `Login` and `PredictionRequest` with immediate field validation.
4. **Maintenance Work Order Flow**:
   - Connect the **"Schedule Maintenance Now"** button in `FinancialImpactCard` to a functional modal that dispatches `POST /api/v1/work-orders`.
5. **Testing**:
   - Vitest unit tests for hooks, form validation, and dashboard components.

---

## Milestone 5: Docker Containerization & Local Development Setup

**Status**: Planned. Docker cannot currently be used on this workstation; build
and PostgreSQL integration checks must run on an authorized machine or in CI.

### Objective
Provide a reproducible, multi-service local environment using multi-stage Dockerfiles and Docker Compose.

### Affected Files
- `backend/Dockerfile` (Multi-stage build, non-root user, healthcheck)
- `frontend/Dockerfile` (Multi-stage build, Vite build -> Nginx SPA serve)
- `docker-compose.yml` (Postgres, Backend API, Frontend, optional MLflow)
- `docker-compose.override.yml` (Development mounts)
- `scripts/dev.ps1`, `scripts/dev.sh`

### Deliverables & Tasks
1. **Optimized Dockerfiles**:
   - Multi-stage builds minimizing image sizes (<150MB for frontend, <350MB for backend).
   - Non-root user execution for container security.
2. **Docker Compose Orchestration**:
   - Networked services: `frontend` (port 80/5173), `backend` (port 8000), `postgres` (port 5432).
   - Named volumes for database persistence.
   - Healthcheck dependencies (`depends_on: { condition: service_healthy }`).
3. **Developer Ergonomics**:
   - One-command startup script: `docker compose up --build`.

---

## Milestone 6: Automated CI/CD Pipelines (GitHub Actions)

**Status**: Planned. Resolve the current frontend lint setup before making it
a required CI gate.

### Objective
Implement enterprise CI/CD pipelines enforcing code quality gates, automated test execution, ML model validation, and container builds.

### Affected Files
- `.github/workflows/ci.yml` (Continuous Integration)
- `.github/workflows/ml-pipeline.yml` (ML validation & retraining)
- `.github/workflows/cd.yml` (Container build & deployment smoke tests)

### Deliverables & Tasks
1. **Continuous Integration (`ci.yml`)**:
   - Trigger on Pull Requests and pushes to `main`.
   - Parallel jobs: Frontend Lint + TypeScript check + Vitest; Backend Flake8/Ruff + Pytest with coverage.
2. **ML Pipeline (`ml-pipeline.yml`)**:
   - Triggerable manually via `workflow_dispatch`.
   - Runs data validation, model retraining, baseline comparison, and gates promotion on PR-AUC threshold.
3. **Continuous Deployment (`cd.yml`)**:
   - Builds production container images on merge to `main`.
   - Publishes to GitHub Container Registry (`ghcr.io`).

---

## Milestone 7: Cloud Infrastructure as Code (Azure Bicep) & Zero-Cost Architecture

### Objective
Define cloud infrastructure in declarative Azure Bicep targeting free-tier / zero-cost services with automated deployment and teardown instructions.

### Affected Files
- `infra/main.bicep` (Root IaC template)
- `infra/modules/container-app.bicep` (Azure Container Apps on Consumption plan)
- `infra/modules/static-web-app.bicep` (Azure Static Web Apps Free tier)
- `infra/deploy.ps1`, `infra/deploy.sh`
- `infra/teardown.ps1`, `infra/teardown.sh`
- `docs/COST_ESTIMATION.md`

### Deliverables & Tasks
1. **Azure Bicep IaC**:
   - Zero-cost Consumption plan configuration (`minReplicas = 0` for scale-to-zero).
   - Azure Static Web App configuration for frontend.
2. **Cost Safety & Teardown**:
   - Strict budget alerts documentation.
   - One-command teardown script to delete the resource group instantly.

---

## Milestone 8: Technical Documentation & Interview Preparation Package

### Objective
Complete documentation explaining architecture, trade-offs, ML decisions, and system design talking points for technical interviews.

### Affected Files
- `README.md` (Comprehensive root documentation)
- `docs/API_DOCUMENTATION.md` (OpenAPI specification & endpoint guide)
- `docs/ML_PIPELINE.md` (Data dictionary, feature engineering, and MLOps guide)
- `docs/MODEL_CARD.md` (Intended use, limitations, metrics, bias)
- `docs/DEPLOYMENT.md` (Local Docker and Azure deployment guide)
- `docs/CI_CD.md` (Pipeline architecture & quality gates)
- `docs/INTERVIEW_TALKING_POINTS.md` (SDE & MLE interview answers & trade-offs)
