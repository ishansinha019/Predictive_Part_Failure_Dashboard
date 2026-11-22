# System Architecture: Current vs. Target Production

**Project Name**: Predictive Part Failure Dashboard (PPFD)  
**Document Version**: 2.0  
**Status**: Approved Architecture Blueprint  

---

## 1. Architectural Evolution Overview

The PPFD system transitions from a prototype/POC architecture to an **interview-grade, production-style, cloud-ready architecture**.

### 1.1 Current Architecture (Prototype State)

```mermaid
flowchart TD
    subgraph Client["Frontend (Vite / React 18)"]
        UI["Ad-hoc Components<br/>CSS Modules + Tailwind"]
        R_STORE["Redux Toolkit<br/>Auth + LocalStorage"]
        AXIOS["Axios Instance<br/>Direct useEffect calls"]
    end

    subgraph Server["Backend (FastAPI)"]
        ROUTERS["app/api/v1/*<br/>Flat Routers"]
        SERVICES["ml_loader.py<br/>Uncached/Direct Joblib load"]
        DB_MODELS["Single Table<br/>PredictionLog"]
    end

    subgraph DataStore["Storage Layer"]
        SQLITE["SQLite (sql_app.db)<br/>Direct metadata.create_all"]
        MODEL_FILE["Local Joblib<br/>models/v1.0/model.joblib"]
    end

    UI --> R_STORE
    UI --> AXIOS
    AXIOS -->|REST over HTTP| ROUTERS
    ROUTERS --> SERVICES
    SERVICES --> MODEL_FILE
    ROUTERS --> DB_MODELS
    DB_MODELS --> SQLITE
```

### 1.2 Target Production Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Application (React 18 + TypeScript + Vite)"]
        ROUTER["React Router v6<br/>Protected & Public Routes"]
        TANSTACK["TanStack Query v5<br/>Server-State Cache & Deduplication"]
        REDUX["Redux Toolkit<br/>Client-Side Session Only"]
        RHF["React Hook Form + Zod<br/>Typed Form Validation"]
        SHADCN["shadcn/ui + Tailwind CSS<br/>Design System & Accessibility"]
    end

    subgraph APILayer["Core Application Backend (FastAPI Production Layout)"]
        MIDDLEWARE["Middleware Stack<br/>Correlation ID, Request Timing, CORS"]
        AUTH_GUARD["OAuth2 + JWT Security<br/>Role-Based Access Control"]
        API_ROUTERS["API Version 1 Controllers<br/>Pydantic v2 DTO Validation"]
        SVC_LAYER["Domain Service Layer<br/>Auth, Machine, Prediction, WorkOrder"]
        REPO_LAYER["Repository Layer<br/>SQLAlchemy 2.0 Typed Queries"]
    end

    subgraph MLLayer["MLOps & Inference Subsystem"]
        ML_SERVICE["Model Inference Service<br/>Thread-Safe Singleton Cache"]
        PIPELINE["Reproducible Pipeline<br/>Pandera → Sklearn → XGBoost"]
        MLFLOW["MLflow Tracking & Registry<br/>Metrics, Artifacts & Baselines"]
        MODEL_CARD["Model Card & Versioning<br/>Metadata & Drift Detection"]
    end

    subgraph DataLayer["Persistence & Storage Layer"]
        POSTGRES["PostgreSQL Relational DB<br/>Normalized Entities & FK Indexes"]
        ALEMBIC["Alembic Migrations<br/>Versioned Schema Evolution"]
    end

    subgraph DevOps["Cloud & DevOps (Azure & GitHub)"]
        GHA["GitHub Actions CI/CD<br/>Lint, Test, ML Evaluation, Deploy"]
        ACA["Azure Container Apps<br/>Consumption Plan (Scale-to-Zero)"]
        SWA["Azure Static Web Apps<br/>Global CDN (Free Tier)"]
        GHCR["GitHub Container Registry<br/>Zero-Cost Image Storage"]
        BICEP["Azure Bicep IaC<br/>Declarative Resource Definitions"]
    end

    ClientLayer -->|HTTPS + Bearer Token| MIDDLEWARE
    MIDDLEWARE --> AUTH_GUARD
    AUTH_GUARD --> API_ROUTERS
    API_ROUTERS --> SVC_LAYER
    SVC_LAYER --> REPO_LAYER
    REPO_LAYER --> ALEMBIC
    ALEMBIC --> POSTGRES
    SVC_LAYER --> ML_SERVICE
    ML_SERVICE --> PIPELINE
    PIPELINE --> MLFLOW
    PIPELINE --> MODEL_CARD

    GHA --> GHCR
    GHCR --> ACA
    GHA --> SWA
    BICEP -.-> ACA
    BICEP -.-> SWA
```

---

## 2. Layer-by-Layer Architectural Breakdown

### 2.1 Frontend Architecture

#### Core Tech Stack
- **Framework**: React 18 + TypeScript + Vite.
- **Server State**: **TanStack Query (React Query) v5** for all API data fetching, caching, query invalidation, and optimistic mutations. Eliminates boilerplate `useEffect` and race conditions.
- **Client State**: **Redux Toolkit** restricted to purely client-side session state (user identity, JWT token, navigation UI state).
- **Design System & Styling**: **Tailwind CSS + shadcn/ui** primitives (built on Radix UI for accessibility: Dialogs, Badges, Tooltips, Metric Cards, Select, Tables).
- **Form Management**: **React Hook Form** paired with **Zod schemas** for compile-time and runtime validation.
- **Data Visualization**: **Recharts** wrapped in responsive, accessible theme-aware card containers.

#### Directory Layout
```
frontend/src/
├── app/                  # Redux store & root TanStack Query client
├── api/                  # Axios base client, auth interceptors & endpoints
├── components/
│   ├── common/           # ProtectedRoute, PublicRoute, ErrorBoundary
│   ├── layout/           # AppNavbar, Sidebar, PageContainer, Footer
│   └── ui/               # Reusable shadcn/ui primitives (Button, Card, Badge, Table, Input)
├── features/
│   ├── authentication/   # LoginForm, authSlice, useAuth hook, authApi
│   ├── fleet/            # MachineCard, MachineGrid, FleetFilters, useFleetMachines
│   ├── predictions/      # PredictionForm, RiskGauge, HistoryChart, usePredictions
│   ├── reliability/      # ReliabilityChart, PartReliabilityProfile, usePartStats
│   └── maintenance/      # FinancialImpactCard, WorkOrderModal, useWorkOrders
├── hooks/                # Global utility hooks (useDebounce, useMediaQuery)
├── types/                # Strongly typed TypeScript interfaces and Zod schemas
└── pages/                # Route entry views (LoginPage, FleetPage, MachineDetailPage)
```

---

### 2.2 Backend Architecture

#### Core Tech Stack
- **Framework**: **FastAPI** running on Python 3.13 with Uvicorn.
- **ORM & Database**: **SQLAlchemy 2.0 (Declarative)** with **Alembic** migrations.
- **Validation**: **Pydantic v2** (`from_attributes = True`, strict typing).
- **Authentication**: OAuth2 Password Bearer with JWT (`python-jose`), bcrypt password hashing (`passlib`), and role-based route dependencies (`Admin`, `Technician`, `Viewer`).
- **Telemetry**: Request correlation IDs (`X-Correlation-ID`), structured JSON logging (`structlog` or standard logging filter), and latency timing headers (`X-Process-Time`).

#### Directory Layout
```
backend/
├── alembic/              # Database migration environments & script revisions
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/
│   │   ├── deps.py       # Dependency injection (get_db, get_current_user, require_role)
│   │   └── v1/
│   │       ├── auth.py         # Login, token refresh, current user profile
│   │       ├── machines.py     # Fleet CRUD, pagination, filtering, history
│   │       ├── parts.py        # Part catalog & reliability distributions
│   │       ├── predictions.py  # Model inference endpoint & prediction audit log
│   │       ├── simulation.py   # Daily fleet wear-and-tear simulation
│   │       └── work_orders.py  # Maintenance work order creation & tracking
│   ├── core/
│   │   ├── config.py     # Pydantic BaseSettings loading .env
│   │   ├── security.py   # Password hashing & JWT generation/validation
│   │   ├── logging.py    # Structured JSON log formatting
│   │   └── middleware.py # Request correlation & process timing
│   ├── db/
│   │   ├── database.py   # Engine, connection pooling, session generator
│   │   └── base.py       # Base model imports for Alembic auto-discovery
│   ├── models/           # SQLAlchemy Declarative Models
│   │   ├── user.py
│   │   ├── machine.py
│   │   ├── part.py
│   │   ├── prediction_log.py
│   │   └── work_order.py
│   ├── repositories/     # Data access abstraction
│   │   ├── machine_repo.py
│   │   └── prediction_repo.py
│   ├── schemas/          # Pydantic v2 DTOs (Request / Response)
│   │   ├── machine.py
│   │   ├── part.py
│   │   ├── prediction.py
│   │   ├── user.py
│   │   └── work_order.py
│   ├── services/         # Domain Business Logic
│   │   ├── auth_service.py
│   │   ├── ml_service.py # Inference & caching layer
│   │   └── simulation_service.py
│   └── main.py           # Application factory, middleware & health routes
├── tests/                # Pytest automated test suite
├── seed_db.py            # Reproducible database seeder
└── requirements.txt
```

---

### 2.3 Machine Learning Architecture & MLOps Pipeline

#### Pipeline Stages
```mermaid
flowchart LR
    A["1. Data Ingestion<br/>CSV / DB Extraction"] --> B["2. Data Validation<br/>Pandera Schema Checks"]
    B --> C["3. Preprocessing<br/>Feature Engineering Pipeline"]
    C --> D["4. Baseline Evaluation<br/>Dummy & Logistic Models"]
    D --> E["5. Candidate Model<br/>XGBoost (Class-Weighted)"]
    E --> F["6. MLflow Tracking<br/>Params, ROC-AUC, PR-AUC"]
    F --> G["7. Model Card & Gate<br/>Automated Quality Threshold"]
    G --> H["8. Export & Version<br/>v1.x joblib Artifact"]
```

1. **Data Validation (Pandera)**: Validates input columns, non-null constraints, and numeric ranges (`time_in_service_days >= 0`, `part_failed in [0, 1]`) before any training step runs.
2. **Feature Engineering**:
   - `machine_type`: Extracted prefix (`M` or `H`).
   - `service_type`: Retained with aligned categorical levels.
   - Categorical Encoding: Scikit-learn `OneHotEncoder(handle_unknown='ignore')`.
3. **Model Selection & Baselines**:
   - Baseline 1: `DummyClassifier(strategy='stratified')`.
   - Baseline 2: `LogisticRegression(class_weight='balanced')`.
   - Production Model: `XGBClassifier(scale_pos_weight=5, eval_metric='logloss')`.
   - Evaluation Metrics: **PR-AUC**, **ROC-AUC**, **Precision**, **Recall on Class 1 (Failures)**. Accuracy is explicitly deprioritized due to class imbalance.
4. **Experiment Tracking**: Integrated with **MLflow** for local tracking of experiments, metrics, run tags, and model versions.
5. **Inference Guarding**:
   - The inference service in `backend/app/services/ml_service.py` loads the fitted bundle (`model`, `encoder`, `feature_columns`) into memory once.
   - Inference aligns feature vectors against `feature_columns` to ensure zero training-serving skew.

---

### 2.4 Relational Database Architecture

```mermaid
erDiagram
    USERS ||--o{ WORK_ORDERS : creates
    MACHINES ||--o{ PREDICTION_LOGS : has
    PARTS ||--o{ PREDICTION_LOGS : evaluates
    MACHINES ||--o{ WORK_ORDERS : targets
    PARTS ||--o{ WORK_ORDERS : replaces

    USERS {
        int id PK
        string username UK
        string hashed_password
        string role
        datetime created_at
    }

    MACHINES {
        string id PK "e.g. M-1001, H-256"
        string machine_type "M or H"
        string status "Operational, Maintenance, Offline"
        datetime install_date
        datetime last_maintenance_date
    }

    PARTS {
        string id PK "e.g. P-BRG-02"
        string category "Bearing, Sensor, Valve, Motor, Controller"
        string name
        int expected_lifespan_days
        float unit_cost
        float planned_repair_hours
        float unplanned_repair_hours
    }

    PREDICTION_LOGS {
        int id PK
        string machine_id FK
        string part_id FK
        int time_in_service_days
        float prediction_score
        string recommendation
        datetime prediction_timestamp
    }

    WORK_ORDERS {
        int id PK
        string machine_id FK
        string part_id FK
        int user_id FK
        string status "Open, In_Progress, Completed"
        string priority "Low, Medium, Critical"
        float estimated_cost
        datetime created_at
        datetime scheduled_date
    }
```

---

### 2.5 Cloud & DevOps Architecture (Azure Zero-Cost Target)

```mermaid
flowchart TD
    subgraph Repo["GitHub Repository"]
        CODE["Main Branch Code"]
        ACTIONS["GitHub Actions Workflows"]
    end

    subgraph CI["Automated CI/CD Pipeline"]
        LINT["Code Lint & Typecheck"]
        TEST["Frontend & Backend Tests"]
        EVAL["ML Validation Gate"]
        BUILD["Docker Multi-Stage Build"]
    end

    subgraph Registry["Container Registry"]
        GHCR["GitHub Container Registry (Free)"]
    end

    subgraph Azure["Microsoft Azure (Free Allowance Architecture)"]
        SWA["Azure Static Web Apps (Free)<br/>Hosts React Frontend globally"]
        ACA["Azure Container Apps (Consumption Plan)<br/>Hosts FastAPI Backend (Scales to 0)"]
    end

    subgraph ExternalDB["Cloud PostgreSQL (Free Tier)"]
        SUPABASE["Supabase / Neon Free PostgreSQL<br/>500MB allowance, zero compute cost"]
    end

    CODE --> ACTIONS
    ACTIONS --> LINT --> TEST --> EVAL --> BUILD
    BUILD --> GHCR
    GHCR --> ACA
    ACTIONS --> SWA
    ACA --> SUPABASE
```

#### Cost Mitigation Strategy:
- **Frontend**: Hosted on **Azure Static Web Apps (Free Plan)**: \$0/month.
- **Backend API**: Hosted on **Azure Container Apps (Consumption)** with `minReplicas = 0`. First 180,000 vCPU-seconds and 360,000 GiB-seconds are free each month: \$0/month for normal testing/interview traffic.
- **Database**: Free-tier cloud PostgreSQL instance (Supabase or Neon): \$0/month.
- **Container Registry**: **GitHub Container Registry (ghcr.io)**: Unlimited public containers, avoids Azure ACR fees (\$5/month saved).
- **IaC**: 100% defined in **Azure Bicep** (`infra/main.bicep`) with automated teardown scripts (`infra/teardown.sh`).
