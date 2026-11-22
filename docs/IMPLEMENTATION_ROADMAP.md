# Implementation Roadmap: Production Transformation

**Project Name**: Predictive Part Failure Dashboard (PPFD)  
**Execution Strategy**: Milestone-Based Incremental Delivery  
**Document Version**: 2.0  

---

## Roadmap Strategy & Principles

1. **Incremental Delivery Without Regression**: Existing user flows (Login, Fleet Overview, Machine Detail, Prediction Form, Charts) will remain functional at every stage.
2. **Interview-Grade Engineering**: Every milestone directly addresses topics probed in technical interviews (system design, REST API best practices, MLOps, containerization, CI/CD, cloud architecture).
3. **Reproducibility**: Every layer must have automated verification and documented local commands.

---

## Milestone 1: Backend Architecture, Relational Modeling & Authentication

### Objective
Replace the prototype database setup and mock authentication with a secure, normalized, production-grade foundation using SQLAlchemy 2.0, Alembic migrations, PostgreSQL compatibility, and real bcrypt JWT security.

### Affected Files
- `backend/app/db/database.py`, `backend/app/db/base.py`
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
   - Associate foreign keys and composite indexes in `PredictionLog`.
2. **Alembic Migration Setup**:
   - Initialize Alembic environment.
   - Generate initial migration revision `001_initial_schema`.
3. **Production Authentication & Security**:
   - Real bcrypt hashing and verification in `app/core/security.py`.
   - Dependency `get_current_user` checking JWT signature, expiry, and user existence in DB.
   - Seed default initial users (`admin` / `technician`) with hashed passwords.
4. **Middleware & Health Probes**:
   - Add Correlation ID (`X-Correlation-ID`) and request execution timer (`X-Process-Time`) middleware.
   - Add `/healthz` and `/readyz` probes.
5. **Testing**:
   - Pytest suite covering token generation, password hashing, invalid credentials, and database constraints.

---

## Milestone 2: Machine Learning Engineering Pipeline & Model Registry

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
   - Evaluate against `XGBClassifier` using PR-AUC, ROC-AUC, Recall (Class 1), and F1-score.
3. **MLflow Experiment Tracking**:
   - Log runs, parameters (`scale_pos_weight`, `learning_rate`, `max_depth`), metrics, and feature importances.
4. **Training-Serving Skew Elimination**:
   - Bundle preprocessor and model into a single unified sklearn Pipeline object.
   - Export versioned artifact with explicit metadata schema.
5. **Testing**:
   - Unit tests verifying: no future data leakage in train/test splits, deterministic inference outputs, and handling of unseen categorical values.

---

## Milestone 3: Clean API Services, Repositories & Work Order Lifecycle

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
