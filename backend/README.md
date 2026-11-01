# MPLADS Backend API Service
**Smart India Hackathon (SIH) 2026**  
**Framework**: FastAPI 0.116+ | SQLAlchemy 2.0+ | Pydantic v2 | PostgreSQL 16+  
**Status**: Database-backed research prototype; validation depends on the configured database and test scope.

> [!IMPORTANT]
> **Data Grounding**: This FastAPI backend directly connects to and serves configured data from the **PostgreSQL database (`mplads_db`) created and validated in Phase 3**. It does not mock data, invent incompatible columns, or overwrite existing tables. All models, queries, and aggregations strictly conform to the 13 relational tables and 8 analytical views established in Phase 3.

---

## 1. Project Architecture

The backend implements a decoupled, modular **Clean Architecture** with strict separation of concerns across four key layers:

```
                                  Client Applications
                     (React / Next.js / Vite / Mobile / External API)
                                           │
                                           ▼ HTTP / JSON (CORS-enabled)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  1. PRESENTATION & ROUTING LAYER (`app/routes/`)                                            │
│     - FastAPI APIRouters with path/query parameter validation (bounds, patterns, types)    │
│     - Endpoints: /health, /projects, /projects/{id}, /analytics, /high-risk                │
│     - Automatic OpenAPI 3.1 & Swagger/ReDoc generation                                      │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  2. DATA CONTRACTS & VALIDATION LAYER (`app/schemas/`)                                     │
│     - Pydantic v2 BaseModel & ConfigDict(from_attributes=True)                              │
│     - Strict input sanitization (ProjectCreate, ProjectUpdate)                              │
│     - Strongly typed output DTOs (ProjectSummary, ProjectDetail, AnalyticsSummaryResponse) │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  3. BUSINESS LOGIC & SERVICE LAYER (`app/services/`)                                       │
│     - Encapsulated database operations (zero SQL/ORM inside route handlers)               │
│     - ProjectService: FTS search, multi-criteria filtering, cursor/offset pagination       │
│     - AnalyticsService: Portfolio KPIs, sector aggregates, risk ranking, fiscal metrics    │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  4. DATA ACCESS & PERSISTENCE LAYER (`app/models/`, `app/database.py`)                     │
│     - SQLAlchemy 2.0 Declarative ORM Models (State, Project, Financial, Progress, Risk)     │
│     - Connection pool: Pre-ping health check, max overflow, connection recycling           │
│     - Dependency injection: `get_db` yielding auto-closing, transaction-safe sessions      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼ PostgreSQL 16+ Protocol
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  Phase 3 PostgreSQL Database (`mplads_db`)                                                  │
│  - 13 Relational Tables: states, constituencies, projects, financials, progress, etc.       │
│  - 8 Materialized / Analytical Views: v_high_risk_projects, v_delayed_projects, etc.        │
│  - Accelerated Indexes: GIN TSVECTOR full-text search, B-Tree, pg_trgm trigrams            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py                          # Application package marker
│   ├── main.py                              # FastAPI app entry point, CORS, lifespan & health probe
│   ├── config.py                            # Pydantic-settings configuration (.env loader)
│   ├── database.py                          # SQLAlchemy engine, SessionLocal, get_db dependency
│   ├── models/                              # SQLAlchemy 2.0 ORM models
│   │   ├── __init__.py                      # Model exports
│   │   └── project.py                       # Dimension, Project, Financial, Progress, Risk, History
│   ├── schemas/                             # Pydantic v2 validation & response DTOs
│   │   ├── __init__.py                      # Schema exports
│   │   └── project.py                       # ProjectSummary, ProjectDetail, Analytics, HighRisk
│   ├── routes/                              # API endpoint definitions
│   │   ├── __init__.py                      # Router exports
│   │   ├── projects.py                      # /projects, /projects/{id}, /projects/search
│   │   └── analytics.py                     # /analytics, /high-risk, /kpis, /sectors, /delayed
│   └── services/                            # Business logic & query execution
│       ├── __init__.py                      # Service exports
│       ├── project_service.py               # Filtering, full-text search, pagination, timeline
│       ├── analytics_service.py             # Analytical view queries, risk scoring aggregations
│       ├── risk_engine.py                   # Centralized Phase 7 Risk Aggregation Engine
│       └── risk/                            # Phase 6 independent detector modules
│           ├── base.py                      # BaseRiskDetector contract & RiskDetectorResult
│           ├── cost_anomaly.py              # Cost Anomaly Detector (Tukey IQR peer statistics)
│           ├── delay_detector.py            # Schedule Delay Slippage Detector
│           ├── fund_utilization.py          # Fund Absorption & Overrun Detector
│           ├── progress_mismatch.py         # Financial vs Physical Divergence Detector
│           ├── duplicate_detection.py       # Semantic Text Duplication (all-MiniLM-L6-v2)
│           └── risk_runner.py               # Safe isolated multi-detector runner
├── tests/                                   # Automated test suite (115 passing tests)
│   ├── __init__.py
│   ├── test_api.py                          # Integration tests using TestClient
│   ├── test_live_server.py                  # Live server end-to-end tests
│   ├── test_risk_detectors.py               # Phase 6 independent detector tests
│   ├── test_risk_engine.py                  # Phase 7 centralized risk engine tests
│   └── verify_live_server.py                # Standalone live verification script
├── requirements.txt                         # Pinned production dependencies
├── .env.example                             # Environment variable template
└── README.md                                # This documentation
```

---

## 2. PostgreSQL Configuration

The backend connects directly to the PostgreSQL database initialized during Phase 3.

* **Database Name**: `mplads_db`
* **Default Port**: `5432`
* **Driver**: `psycopg2-binary` via `postgresql+psycopg2://`
* **Tables Served**:
  * `states`: 36 official States and Union Territories
  * `constituencies`: 543 Lok Sabha Parliamentary constituencies
  * `projects`: Master project registry with full-text search vectors
  * `financials`: Sanctioned amounts, released funds, expenditures, and utilization
  * `progress`: Physical progress %, milestones, days delayed, inspection logs
  * `risk_scores`: Machine-learning / algorithmic risk scores (0–100) and risk tiers
  * `risk_factors`: Causal factor breakdowns, weights, impacts, and mitigation recommendations
  * `project_history`: Append-only audit trail and status transition ledger
  * `union_budget_expenditure`: 33-year Ministry Demand No. 91 fiscal history (1993–2025)
* **Views Queried**:
  * `v_project_master`: 360-degree project overview combining financials, progress, and risk
  * `v_high_risk_projects`: Projects with elevated delay/cost overrun risk, sorted descending
  * `v_delayed_projects`: Stalled and delayed project surveillance
  * `v_sector_summary`: Sectoral allocations, expenditure, and average progress
  * `v_state_allocations`: State-level release vs. expenditure equity
  * `v_missing_info_audit`: Governance compliance checks for missing data
  * `v_state_sc_st_equity`: 15% SC / 7.5% ST statutory allocation monitoring
  * `v_state_efficiency_ranking`: Utilization and completion rate rankings across States

---

## 3. Environment Variable Setup

The backend uses `pydantic-settings` to safely read configuration from environment variables or a local `.env` file. Zero credentials are hardcoded.

### Configuration Template (`backend/.env.example`)

```ini
# =============================================================================
# FastAPI Backend Configuration for MPLADS Project
# Copy this file to .env in backend/ or the project root.
# DO NOT commit .env with real passwords to version control.
# =============================================================================

# Database Connection URL (Recommended for SQLAlchemy)
DATABASE_URL=postgresql+psycopg2://your_postgres_username:your_secure_password@localhost:5432/mplads_db

# Alternative Individual Database Parameters (Fallback if DATABASE_URL is not set)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mplads_db
DB_USER=your_postgres_username
DB_PASSWORD=your_secure_password

# Application Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
API_V1_STR=/api/v1
PROJECT_NAME="MPLADS Governance & Analytics Platform API"

# CORS Configuration (comma-separated list of allowed origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# Phase 7 Risk Engine Configuration (Weights must sum to 1.0)
RISK_WEIGHT_COST_ANOMALY=0.25
RISK_WEIGHT_DELAY=0.20
RISK_WEIGHT_FUND_UTILIZATION=0.15
RISK_WEIGHT_PROGRESS_MISMATCH=0.20
RISK_WEIGHT_DUPLICATE_DETECTION=0.20
RISK_ENGINE_VERSION="risk_engine_v1.0"
```

### Setting up `.env`

```bash
# Copy template to .env
cp backend/.env.example backend/.env

# Update credentials for your local PostgreSQL instance
# If PostgreSQL runs locally without password for your user, leave DB_PASSWORD empty
```

---

## 4. Installation Commands

Set up a clean virtual environment and install dependencies:

```bash
# 1. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt
```

### Dependencies Installed (`backend/requirements.txt`)
* `fastapi>=0.115.0`: Core web API framework
* `uvicorn[standard]>=0.30.0`: Production ASGI server with `uvloop`
* `sqlalchemy>=2.0.0`: Database ORM and connection pooling
* `psycopg2-binary>=2.9.9`: PostgreSQL database adapter
* `pydantic>=2.8.0`: Data modeling, serialization, and validation
* `pydantic-settings>=2.4.0`: Typed environment variable parsing
* `python-dotenv>=1.0.0`: `.env` configuration file loader
* `httpx>=0.27.0`: HTTP client for testing and health probes
* `pytest>=8.0.0`: Automated test runner

---

## 5. How to Start the FastAPI Server

Start the ASGI server with **Uvicorn** with automatic live reloading:

### Option A: From the `backend/` Directory (Recommended)
```bash
cd backend
uvicorn app.main:app --reload
```

### Option B: From the Project Root Directory
```bash
uvicorn backend.app.main:app --reload
```

### Option C: Using Python Directly
```bash
cd backend
python -m app.main
```

### Server URLs
* **Swagger Interactive UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Human-Readable UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **OpenAPI 3.1.0 Specification**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
* **System Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 6. API Endpoint Documentation

All endpoints are available at the root path and with the `/api/v1` prefix.

### Health & System Status
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API version, service status, and navigation directory |
| `GET` | `/health` | Live PostgreSQL connectivity check (returns 200 or 503) |
| `GET` | `/api/health` | Canonical API alias for the health probe |

### Projects & Operations (`/projects` & `/api/v1/projects`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects` | Paginated listing with multi-criteria filtering (state, sector, MP, amounts, risk, status) |
| `GET` | `/projects/search` | Full-text natural language search with PostgreSQL `TSVECTOR` and trigram fuzzy matching |
| `GET` | `/projects/{id}` | Complete 360-degree project view (financials, progress, risk score, factors, timeline) |
| `GET` | `/projects/{id}/features` | Engineered predictive risk & governance features (Phase 5) |
| `GET` | `/projects/{id}/risk` | Risk engine assessment (overall score, risk tier, detector breakdown; supports `recalculate=true`) |
| `POST` | `/projects/{id}/risk/recalculate` | Force complete recalculation of all Phase 6 detectors and persist assessment |
| `POST` | `/projects/risk/batch` | Batch recalculation across multiple project IDs or top projects |
| `POST` | `/projects` | Create a new project, initialize financial ledger, and log audit event |
| `GET` | `/projects/{id}/progress` | Retrieve milestone execution trajectory and physical progress |
| `GET` | `/projects/{id}/explanation` | Structured project explainability breakdown (risk level, score, summary, factors, empirical evidence) |
| `GET` | `/projects/{id}/why-flagged` | Concise "Why Was This Flagged?" structured explanation based strictly on triggered detectors |
| `GET` | `/projects/{id}/explain` | Comprehensive explainability audit with UI cards, warning chips, and recommended actions |

### Analytics & Predictive Risk (`/analytics`, `/high-risk`, & `/api/v1/analytics`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics` | Comprehensive governance statistics: total projects, outlays, status distribution, risk distribution, state/district/sector aggregations |
| `GET` | `/high-risk` | High-risk project escalation list with causal risk factors, sorted highest-risk first (supports `limit`) |
| `GET` | `/api/v1/analytics/kpis` | National KPI cards (sanctioned, released, spent in Cr, utilization %, delay count, high risk count) |
| `GET` | `/api/v1/analytics/sectors` | Sector-wise financial allocations, physical progress, and risk breakdown |
| `GET` | `/api/v1/analytics/delayed` | Real-time surveillance of delayed, stalled, and critical milestone works |
| `GET` | `/api/v1/analytics/missing-info` | Compliance audit identifying works with missing dates, uninspected milestones, or missing coordinates |
| `GET` | `/api/v1/analytics/state-equity` | SC/ST statutory quota compliance (15% SC / 7.5% ST) across 36 States/UTs |
| `GET` | `/api/v1/analytics/state-efficiency`| State and UT efficiency rankings by utilization rate and completion rate |
| `GET` | `/api/v1/analytics/budget-history` | 33-year Union Budget Demand No. 91 fiscal performance trends (1993–2025) |

---

## 7. Example Requests & Actual Responses

### 1. Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "backend": "running",
  "database": "connected",
  "database_name": "mplads_db"
}
```

### 2. List Projects with Filtering & Pagination
```bash
curl -X GET "http://127.0.0.1:8000/projects?limit=2&skip=0&sector=Drinking%20Water%20Facilities"
```
**Response (`200 OK`)**:
```json
{
  "items": [
    {
      "project_id": "MPLADS-2024-0001",
      "project_code": "WB-KOL-2024-001",
      "project_title": "Community RO Plant",
      "sector": "Drinking Water Facilities",
      "state_name": "West Bengal",
      "district_name": "Kolkata",
      "mp_name": "Sudip Bandyopadhyay",
      "current_status": "Completed",
      "financial_year": "2024-25",
      "sanctioned_amount": 2500000.0,
      "released_amount": 2500000.0,
      "expenditure_amount": 2450000.0,
      "physical_progress_pct": 100.0,
      "days_delayed": 0,
      "overall_risk_score": 12.5,
      "risk_level": "Low",
      "search_relevance": null
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 2,
  "page": 1,
  "page_size": 2,
  "total_pages": 2
}
```

### 3. 360-Degree Project Detail (`GET /projects/{id}`)
```bash
curl -X GET "http://127.0.0.1:8000/projects/MPLADS-2024-0015"
```
**Response (`200 OK`)**:
```json
{
  "project_id": "MPLADS-2024-0015",
  "project_code": "KA-BAN-2024-003",
  "project_title": "Rejuvenation of Traditional Village Water Pond",
  "project_description": "Desilting, bund strengthening, and solar aeration fountain installation.",
  "sector": "Drinking Water Facilities",
  "state_id": 29,
  "constituency_id": 28,
  "district_name": "Bangalore Rural",
  "implementing_agency": "Rural Development and Panchayat Raj Department",
  "mp_name": "C. N. Manjunath",
  "current_status": "Work Order Issued",
  "financial_year": "2024-25",
  "recommendation_date": "2024-08-01",
  "state": {
    "state_id": 29,
    "state_name": "Karnataka",
    "state_code": "KA"
  },
  "financial": {
    "sanctioned_amount": 1600000.0,
    "released_amount": 800000.0,
    "expenditure_amount": 100000.0,
    "unspent_balance": 700000.0,
    "utilization_pct": 12.5
  },
  "risk_score": {
    "overall_risk_score": 42.0,
    "risk_level": "Moderate",
    "delay_risk_score": 45.0,
    "cost_overrun_risk_score": 38.0
  }
}
```

### 4. High-Risk Projects Escalation (`GET /high-risk`)
```bash
curl -X GET "http://127.0.0.1:8000/high-risk?limit=2"
```
**Response (`200 OK`)**:
```json
[
  {
    "project_id": "MPLADS-2024-0005",
    "project_code": "MH-MUM-2024-001",
    "project_title": "Construction of Cement Concrete Road & Drain",
    "state_name": "Maharashtra",
    "district_name": "Mumbai Suburban",
    "mp_name": "Piyush Goyal",
    "sector": "Roads, Pathways and Bridges",
    "current_status": "Stalled",
    "overall_risk_score": 78.5,
    "delay_risk_score": 85.0,
    "cost_overrun_risk_score": 72.0,
    "risk_level": "High",
    "confidence_score": 0.92,
    "sanctioned_amount": 4500000.0,
    "days_delayed": 65,
    "important_risk_factors": [
      {
        "category": "Contractor Inaction",
        "factor": "Contractor Default on Foundation Milestone",
        "weight": 0.45,
        "impact": "Critical",
        "recommendation": "Issue final contractual show-cause notice and invoke bank guarantee if unresponsive within 14 days."
      }
    ]
  }
]
### 5. Project Explainability (`GET /projects/{id}/explanation`)
```bash
curl -X GET "http://127.0.0.1:8000/projects/MPLADS-2024-0010/explanation"
```
**Response (`200 OK`)**:
```json
{
  "project_id": "MPLADS-2024-0010",
  "risk_level": "MODERATE",
  "risk_score": 44.6,
  "summary": "Project flagged due to delay, progress mismatch, and agency friction.",
  "factors": [
    {
      "name": "Delay Detection",
      "detector": "delay_detection",
      "triggered": true,
      "severity": "critical",
      "contribution": 20.0,
      "evidence": [
        {
          "text": "Project is delayed by 512 days.",
          "actual_value": 512,
          "reference_value": 0,
          "unit": "days"
        }
      ]
    },
    {
      "name": "Progress Mismatch",
      "detector": "progress_mismatch",
      "triggered": true,
      "severity": "high",
      "contribution": 13.8,
      "evidence": [
        {
          "text": "Physical progress exceeds financial progress by 45 percentage points.",
          "actual_value": 20.0,
          "reference_value": 65.0,
          "unit": "percentage points"
        }
      ]
    },
    {
      "name": "Agency Pattern",
      "detector": "agency_pattern",
      "triggered": true,
      "severity": "medium",
      "contribution": 10.8,
      "evidence": [
        {
          "text": "Agency 'District Rural Development Agency (DRDA)' historical delay rate is 60% across 20 projects.",
          "actual_value": 60.0,
          "reference_value": 25.0,
          "unit": "%"
        }
      ]
    }
  ]
}
```

### 6. Nonexistent Project Handling (404 Not Found)
```bash
curl -X GET "http://127.0.0.1:8000/projects/NONEXISTENT-PROJECT-9999"
```
**Response (`404 Not Found`)**:
```json
{
  "detail": "Project with ID 'NONEXISTENT-PROJECT-9999' not found."
}
```

### 7. Parameter Validation (422 Unprocessable Entity)
```bash
curl -X GET "http://127.0.0.1:8000/projects?limit=-1"
```
**Response (`422 Unprocessable Entity`)**:
```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "limit"],
      "msg": "Input should be greater than or equal to 1",
      "input": "-1",
      "ctx": {"ge": 1}
    }
  ]
}
```

---

## 8. Swagger & Interactive Documentation

FastAPI automatically generates interactive OpenAPI documentation:

* **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
  Explore all 35 endpoints, view parameter schemas, and test live queries directly from your browser.
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  
  Publication-ready, clean hierarchical API documentation.
* **OpenAPI 3.1.0 JSON Specification**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 9. Health-Check Endpoint

* **URL**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (or `/api/health`)
* **Method**: `GET`
* **Health Check Behavior**:
  * Actively runs a lightweight `SELECT 1` SQL query against PostgreSQL through the connection pool.
  * Returns `HTTP 200 OK` with status metadata if the database is responding.
  * Returns `HTTP 503 Service Unavailable` if the database connection drops or times out.

---

## 10. Testing Instructions

The repository includes four comprehensive test suites covering API functionality, live server verification, independent Phase 6 risk detectors, and the Phase 7 centralized risk engine.

### Running Test Suites Individually
```bash
cd backend

# 1. API Route Integration Tests (30 tests)
pytest tests/test_api.py -v

# 2. Phase 6 Independent Risk Detectors (23 tests)
pytest tests/test_risk_detectors.py -v

# 3. Phase 7 Centralized Risk Engine (39 tests)
pytest tests/test_risk_engine.py -v

# 4. Live Server End-to-End Tests (23 tests)
pytest tests/test_live_server.py -v
```

### Running the Entire Backend Test Suite
```bash
cd backend
pytest tests/ -v
```

**Verified Test Results**:
```
============================== test session starts ===============================
tests/test_api.py ..............................                         [ 26%]
tests/test_live_server.py .......................                        [ 46%]
tests/test_risk_detectors.py .......................                     [ 66%]
tests/test_risk_engine.py .......................................        [100%]
====================== 115 passed, 66 warnings in 1.66s =======================
```
* **Passed**: 115 / 115 tests (100% pass rate)
* **Failed**: 0
* **SQLAlchemy Errors**: 0
* **Data Mismatches**: 0

## Interpreting verification evidence

The [root guide](../README.md) distinguishes offline feature tests from database integration checks. Run the relevant tests in [tests](tests) against a disposable configured database and inspect fixture requirements first. Do not infer deployment readiness or dataset provenance from an architectural phase label. No production acceptance or fresh integration run is asserted by this documentation update.
