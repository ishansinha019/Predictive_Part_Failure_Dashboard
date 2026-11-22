# Architecture Decision Records (ADRs) & Technical Trade-offs

**Project Name**: Predictive Part Failure Dashboard (PPFD)  
**Document Version**: 2.0  
**Status**: Adopted  

---

## ADR-001: Backend Architecture & Technology Selection

### Context
The original backend was built with FastAPI, SQLite, and Python, directly loading an XGBoost ML model via joblib. The user mentioned an interest in ASP.NET Core Web API while also specifying:
> *"Backend: Use the current backend stacks... For Python-based ML inference, use FastAPI as a separate service only when separation is architecturally justified. Avoid unnecessary microservices... Do not delete working functionality merely to introduce a different architecture."*

Furthermore, our system audit confirmed that the Windows host environment does not have the `.NET SDK` installed (`dotnet` is unrecognized on the system), while Python 3.13 is fully functional.

### Decision
We **retain and elevate the FastAPI backend**, structuring it into an enterprise, cleanly-layered architecture (Controllers &rarr; Services &rarr; Repositories &rarr; ORM) rather than splitting into an artificial microservices split or rewriting in .NET.

### Rationale & Trade-offs
1. **Single-Process Efficiency**: Keeping the core web API and ML model evaluation in the same process eliminates network serialization latency (HTTP/gRPC hop) between a .NET gateway and a Python inference worker. For a fleet of hundreds of machines running periodic inference, in-process inference achieves sub-10ms response times.
2. **Elimination of Multi-Service Overhead**: Running separate web API and inference microservices would double container management overhead, duplicate CI/CD pipelines, and increase cold-start latency on Azure Container Apps.
3. **Interview Talking Point**: In system design interviews, knowing *when not to build microservices* is a strong signal of senior engineering maturity. A modular monolith with clear service/repository boundaries is the recommended starting architecture for systems at this scale.

---

## ADR-002: Server-State vs. Client-State Management (TanStack Query + Redux Toolkit)

### Context
The existing React frontend used Redux Toolkit solely for an `authSlice` storing the user token, while all API data (machine lists, history, part stats) was fetched using raw `useEffect` hooks and stored in local component `useState`. This led to race conditions, zero caching, duplicated network requests, and missing loading/error boundaries.

### Decision
We adopt **TanStack Query (React Query) v5** for all server-state (fetching, caching, invalidation, mutations) while retaining **Redux Toolkit** strictly for client-side session state (auth credentials and global UI preferences).

### Rationale & Trade-offs
1. **Separation of Concerns**:
   - **Server State** (machines, predictions, stats) is asynchronous, shared, potentially stale, and belongs in a cache manager with stale-time, deduplication, and retry policies.
   - **Client State** (active auth token, drawer toggle) is synchronous, local, and belongs in Redux.
2. **Automatic Cache Invalidation**: When a user submits a prediction or creates a work order, TanStack Query immediately invalidates `['machines', machineId, 'history']` and `['workOrders']`, automatically triggering a refetch across all subscribed components without prop drilling or manual re-render triggers.
3. **Alternative Considered**: Managing all server data in Redux Toolkit with `createAsyncThunk`. Rejected because it requires hundreds of lines of boilerplate (`pending`, `fulfilled`, `rejected` reducers, manual normalization, and custom cache expiration logic).

---

## ADR-003: Relational Persistence & Schema Migrations (PostgreSQL + Alembic)

### Context
The existing database implementation used a single SQLite table (`prediction_logs`) created at startup via `Base.metadata.create_all()`. There were no entity models for machines, parts, work orders, or users, no foreign keys, no indexes, and no schema migration tooling.

### Decision
We adopt **PostgreSQL** as the primary relational database (with SQLite retained as a zero-dependency fallback for local offline testing), managed through **SQLAlchemy 2.0 Declarative ORM** and version-controlled with **Alembic**.

### Rationale & Trade-offs
1. **Relational Integrity**: Equipment, parts, prediction logs, and work orders have inherent relational constraints (e.g., a prediction log must reference an existing machine and part; deleting a machine should cascade or restrict related logs).
2. **Production Schema Evolution**: In production, databases cannot be dropped and recreated. Alembic provides deterministic, auditable, forward and backward schema migrations (`alembic upgrade head` / `alembic downgrade`).
3. **Connection Pooling**: SQLAlchemy 2.0 `QueuePool` with health checks (`pool_pre_ping=True`) ensures robust connection management when scaling on containerized infrastructure.

---

## ADR-004: Machine Learning Strategy (XGBoost with Class-Weighting + Pandera + MLflow)

### Context
The dataset exhibits significant class imbalance (~22% failure rate). The original scripts trained an XGBoost model without input validation, baseline comparisons, or experiment tracking. An outdated model artifact in `backend/models` also produced severe training-serving feature skew.

### Decision
1. **Data Validation**: Enforce schemas with **Pandera** before ingestion to validate categorical domain values and non-negative service day constraints.
2. **Baselines & Metrics**: Train a `DummyClassifier` (chance) and `LogisticRegression` (linear) baseline. Evaluate the candidate `XGBClassifier` using **PR-AUC (Precision-Recall Area Under Curve)**, **Recall on Class 1**, and **F1-Score**. Accuracy is explicitly rejected as a primary metric due to class imbalance.
3. **Class Imbalance Strategy**: Use `scale_pos_weight=5` inside XGBoost, which penalizes false negatives (missed equipment failures) 5× more heavily than false positives (premature inspections). In industrial predictive maintenance, an undetected failure (\$22,500 downtime) is orders of magnitude worse than an early planned inspection (\$600).
4. **Experiment Tracking**: Use **MLflow** to track metrics, hyperparameters, and artifacts, generating an automated **Model Card** documenting performance bounds.

---

## ADR-005: Design System & Accessible Component Primitives (Tailwind CSS + shadcn/ui)

### Context
The frontend had visual inconsistencies caused by mixing CSS Modules (`FleetPage.module.css`), inline `style={{ ... }}` objects, and utility Tailwind classes. Common UI elements like dialogs, badges, and cards were duplicated.

### Decision
Adopt a unified **shadcn/ui-inspired component architecture** using **Tailwind CSS** and **Radix UI primitives**.

### Rationale & Trade-offs
1. **Accessibility (a11y)**: Radix UI primitives provide out-of-the-box keyboard navigation, screen reader compliance, ARIA attributes, and focus traps for modals and dropdowns.
2. **Maintainability & Ownership**: Unlike monolithic component libraries (MUI, Ant Design) that inject heavy runtime CSS and rigid styling overrides, shadcn/ui primitives live directly inside `src/components/ui/`, giving 100% control over design tokens.
3. **Visual Hierarchy**: Consistent color palettes (e.g., semantic tokens for `danger` = critical risk, `warning` = moderate wear, `success` = healthy equipment, `muted` = secondary metadata).

---

## ADR-006: Zero-Cost Cloud Deployment (Azure Container Apps + Static Web Apps)

### Context
The user requested practical Azure cloud deployment experience under a strict constraint: **zero-cost / free-tier resources only**, avoiding permanent VM costs, AKS clusters, or paid database tiers.

### Decision
Architect the cloud topology using:
- **Frontend**: **Azure Static Web Apps (Free Plan)** — global CDN, SSL, custom domain support, 100GB bandwidth/month included at \$0.
- **Backend**: **Azure Container Apps (Consumption Plan)** — configured with `minReplicas = 0` (scale-to-zero when idle). The monthly free grant of 180,000 vCPU-seconds and 360,000 GiB-seconds comfortably covers all testing, demonstration, and interview evaluation traffic at \$0.
- **Container Registry**: **GitHub Container Registry (ghcr.io)** — free for public repositories, eliminating Azure Container Registry's \$5/month cost.
- **Database**: Cloud PostgreSQL free tier (Supabase or Neon free 500MB instances) with connection pooling.
- **Infrastructure as Code**: Declarative **Azure Bicep** templates with an automated `teardown.sh` script to guarantee clean destruction.

---

## ADR-007: Automated Testing Strategy (Pytest + Vitest + React Testing Library)

### Context
The repository had zero automated tests across both frontend and backend.

### Decision
Establish an automated test pyramid:
1. **Backend Unit & Integration Tests**: **Pytest** with `httpx` and FastAPI `TestClient`.
   - Test password hashing, token validation, and authorization guards.
   - Test ML prediction service with edge-case feature inputs.
   - Test database queries and work order status state transitions.
2. **Frontend Component & Hook Tests**: **Vitest** + **React Testing Library**.
   - Test form validation rules (Zod schemas).
   - Test TanStack Query cache behavior and UI loading/empty/error states.
   - Test financial impact calculation equations.
3. **ML Pipeline Tests**:
   - Test preprocessing pipeline to verify no NaN outputs, correct column count, and zero training-serving skew.
   - Test that model output is strictly bounded within $[0.0, 1.0]$.
