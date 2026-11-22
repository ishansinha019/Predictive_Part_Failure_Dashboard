# Project Audit & Technical Discovery

**Project Name**: Predictive Part Failure Dashboard (PPFD)  
**Date**: November 2026  
**Auditor**: Senior Full-Stack Software Architect & ML Engineer  
**Repository Path**: `c:\Users\ishan\OneDrive\Desktop\PPFD Project\Predictive_Part_Failure_Dashboard`

---

## 1. Executive Summary

The **Predictive Part Failure Dashboard (PPFD)** is an industrial IoT / predictive maintenance application designed to predict component failures in a fleet of machines (medium-duty `M-` and heavy-duty `H-` equipment). The core business objective is to prevent costly unplanned downtime by alerting maintenance engineers and calculating the financial ROI of proactive part replacement.

While the existing proof-of-concept (POC) demonstrates working end-to-end connectivity between a React frontend, a FastAPI backend, and an XGBoost machine learning model, the codebase is in a **prototype stage**. It lacks automated testing, proper relational database modeling, database migrations, CI/CD, production-grade authentication, structured logging, schema validation, and reproducible ML pipeline infrastructure.

This audit provides a comprehensive breakdown of the existing assets, technical debt, architectural gaps, and a prioritized remediation plan to elevate this repository into an **interview-grade, production-style software system**.

---

## 2. Business Domain & Use Case Discovery

### 2.1 Problem Statement
Industrial equipment breakdowns cause severe operational and financial penalties:
- **Unplanned downtime** costs \$1,500/day in lost output, emergency technician dispatch, and rush shipping for components.
- **Planned maintenance** allows replacing worn components during scheduled downtime, reducing downtime from days to hours and eliminating rush labor.

### 2.2 Target Personas
1. **Maintenance Technicians**: Inspect machine status, run what-if predictions for installed parts based on operating days, and initiate work orders.
2. **Plant / Operations Managers**: Review entire fleet health, identify high-risk machines, and monitor long-term risk trends.
3. **Reliability Engineers**: Study historical failure distributions across component types (`P-BRG-02`, `P-CTR-03`, `P-MTR-05`, `P-SEN-04`, `P-VLV-01`) to optimize scheduled maintenance intervals.
4. **Financial Decision Makers**: Justify maintenance budgets using the dynamic reactive vs. proactive cost ROI calculations.

---

## 3. Subsystem-by-Subsystem Technical Audit

### 3.1 Machine Learning Subsystem (`ml_model/`)

#### Existing Components
- **Dataset**: `ml_model/data/service_history_extended.csv` (300 records, 7 columns: `service_id`, `machine_id`, `part_id`, `service_date`, `time_in_service_days`, `service_type`, `part_failed`).
- **Notebooks**: `1_data_exploration.ipynb` (EDA, class balance checks), `2_data_exploration.ipynb` (feature engineering exploration).
- **Scripts**:
  - `src/preprocess.py`: Extracts `machine_type`, drops ID/date columns, one-hot encodes categorical features (`machine_id`, `part_id`, `service_type`, `machine_type`).
  - `src/train.py`: Trains `XGBClassifier` with `scale_pos_weight=5` to address the ~22% failure class imbalance. Evaluates with classification report and dumps `part_failure_model.joblib`.
- **Pre-trained Artifact**: `saved_model/part_failure_model.joblib` (15 feature columns).

#### Deficiencies & Technical Debt
1. **Training-Serving Skew**:
   - `preprocess.py` extracts `machine_type` and one-hot encodes it, but `ml_loader.py` in the backend was not computing `machine_type`.
   - `service_type` during inference was hardcoded to `"Routine Check"`, which skews model predictions because historical failures only occurred under `"Repair"` or `"Replacement"`.
   - Discrepancy between `backend/models/v1.0/part_failure_model.joblib` (outdated 9-column dummy model) and `ml_model/saved_model/` (15-column model).
2. **Lack of Experiment Tracking**: No MLflow or Weights & Biases integration. Hyperparameters, dataset hash, training duration, PR-AUC, and ROC-AUC are not recorded.
3. **No Baseline Comparison**: The model is trained directly without comparing against a `DummyClassifier` or baseline `LogisticRegression`.
4. **No Data Validation**: No Pandera or Great Expectations schema validation to verify CSV format, null values, or numeric bounds prior to training.
5. **Hardcoded Paths**: Scripts assume execution strictly from specific subdirectories (`data/...` vs `../ml_model/data/...`).
6. **No Automated ML Tests**: Zero unit tests verifying data leakage prevention, encoding consistency, probability bounds, or edge-case handling.

---

### 3.2 Backend Subsystem (`backend/`)

#### Existing Components
- **Framework**: FastAPI with Pydantic and SQLAlchemy ORM.
- **Entrypoint**: `app/main.py` configuring CORS and mounting routers for Auth, Predictions, Machines, Parts, and Simulation.
- **Database**: Single SQLAlchemy model `PredictionLog` in `app/db/models.py`. Direct table creation via `Base.metadata.create_all(bind=engine)`.
- **Scripts**: `seed_db.py` (seeds 300 CSV rows), `generate_synthetic_data.py` (generates 100 random machines).

#### Deficiencies & Technical Debt
1. **Mock / Insecure Authentication**:
   - `POST /api/v1/auth/token` accepts any non-empty username/password.
   - No `User` model, no password hashing verification (even though `passlib[bcrypt]` is in `requirements.txt`).
   - Endpoints do not declare `Depends(get_current_user)` — all business APIs are completely unauthenticated.
2. **Database Modeling Gaps**:
   - Only a single table `prediction_logs` exists.
   - No entity models for `Machine`, `Part`, `WorkOrder`, or `User`.
   - `GET /api/v1/machines/` executes `SELECT DISTINCT machine_id` from logs with hardcoded `"last_updated": "2023-01-01"`.
   - No database migrations (no Alembic). Modifying schema requires dropping the database.
   - SQLite used for development without production connection pooling or thread-safety configurations.
3. **API Contract & Design Issues**:
   - Pydantic v1 `orm_mode = True` syntax used causing runtime deprecation warnings in Pydantic v2.
   - Lack of standard API envelope, error structure, or request correlation IDs (`X-Correlation-ID`).
   - No pagination, sorting, or filtering on `/api/v1/machines/` or `/api/v1/machines/{id}/history`.
   - No health or readiness probes (`/healthz`, `/readyz`).
4. **Windows Security / WDAC Fragility**:
   - Pre-compiled Cython `.pyd` binaries in SQLAlchemy wheels trigger Windows AppLocker / WDAC errors. Must ensure resilient pure-Python execution flags.
5. **No Automated Backend Tests**: No test suite exists. Zero coverage of API endpoints, authentication, simulation, or database queries.

---

### 3.3 Frontend Subsystem (`frontend/`)

#### Existing Components
- **Framework**: React 18 with TypeScript and Vite.
- **State Management**: Redux Toolkit (`authSlice.ts`) managing JWT token and auth state in `localStorage`.
- **Routing**: React Router DOM (`/login`, `/`, `/machine/:machineId`).
- **Data Visualization**: Recharts for `RiskGauge`, `HistoryChart`, and `ReliabilityChart`.
- **Styling**: Tailwind CSS v4 mixed with CSS Modules (`FleetPage.module.css`) and inline styles.

#### Deficiencies & Technical Debt
1. **Server-State Anti-Patterns**:
   - Component-level `useEffect` + `useState` fetching with no request caching, deduplication, automatic retries, or refetch-on-window-focus.
   - TanStack Query (React Query) is missing, leading to manual lifecycle management and boilerplate.
2. **Styling Inconsistencies**:
   - Scattered styling paradigms: CSS Modules, raw Tailwind utility strings, and inline `style={{ ... }}` blocks coexist in the same files.
   - No centralized accessible UI component library (no shadcn/ui or Radix UI primitives).
3. **Form Handling**:
   - Forms use raw controlled inputs with no validation schema (no React Hook Form, no Zod).
   - Error messages are rudimentary.
4. **Hardcoded Logic & Missing Reactivity**:
   - `FinancialImpactCard` previously received hardcoded `failureRisk={0.85}` instead of live model outputs.
   - Lack of debounce on the fleet search filter.
5. **No Frontend Tests**: Zero Vitest or React Testing Library suites. Zero Playwright end-to-end tests.

---

### 3.4 DevOps, Infrastructure & Quality

#### Existing State
- **Containers**: Basic Dockerfiles for backend and frontend. No multi-stage caching, no non-root user security.
- **Docker Compose**: Missing. Cannot spin up database, backend, and frontend with a single command.
- **CI/CD**: No `.github/workflows` directory. Zero automated build or test gates on push/PR.
- **Cloud Infrastructure**: No Infrastructure-as-Code (Azure Bicep / Terraform). No cloud deployment definitions.
- **Documentation**: Root `readme.md` consists of only 2 lines of synthetic data disclaimer.

---

## 4. Technical Debt Severity Matrix

| Component | Technical Debt / Gap | Severity | Effort | Interview Impact |
|---|---|---|---|---|
| **Security** | Fake authentication; all API routes unprotected | **Critical** | Medium | High |
| **Data Architecture** | Single un-normalized table, no Alembic migrations, no real entity models | **High** | Medium | High |
| **ML Engineering** | No experiment tracking (MLflow), no data validation (Pandera), no baselines | **High** | Medium | High |
| **Testing** | 0% test coverage across Python, TypeScript, and React | **Critical** | High | Critical |
| **Frontend Architecture** | Ad-hoc `useEffect` fetches, no TanStack Query, no Zod validation, styling drift | **Medium** | Medium | High |
| **DevOps** | No Docker Compose, no GitHub Actions CI/CD, no Azure Bicep IaC | **High** | Medium | Critical |
| **Observability** | No structured JSON logging, no correlation IDs, no health probes | **Medium** | Low | Medium |
| **Documentation** | Empty README, no architectural diagrams or API documentation | **High** | Low | Critical |

---

## 5. Scope of Transformation

To make this project interview-ready without breaking working features:
1. **Preserve Domain Logic**: Retain the predictive maintenance concept, synthetic fleet structure, and financial impact equations.
2. **Evolve Backend**: Transition FastAPI to a clean feature/service/repository architecture, add proper PostgreSQL persistence with Alembic migrations, secure JWT authentication with password hashing, and add health/metrics endpoints.
3. **Modernize Frontend**: Refactor to TanStack Query for server state, integrate shadcn/ui design tokens and components, add React Hook Form + Zod, and ensure responsive layouts.
4. **Engineer ML Pipeline**: Implement reproducible training with Pandera validation, baseline comparisons, MLflow experiment tracking, evaluation reports, and model cards.
5. **Add Production DevOps**: Implement Docker Compose, complete GitHub Actions (CI, ML training, CD), zero-cost Azure Bicep IaC, and 80%+ test coverage across unit, integration, and E2E suites.
