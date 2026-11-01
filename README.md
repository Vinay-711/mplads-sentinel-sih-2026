# MPLADS Project Intelligence & Governance Database
**Smart India Hackathon (SIH) 2026**  
**Domain**: Ministry of Statistics and Programme Implementation (MoSPI) – Member of Parliament Local Area Development Scheme (MPLADS)  
**Database**: PostgreSQL 16+ with `pg_trgm` & Full-Text Search (FTS)  
**Status**: Research and hackathon prototype; production readiness is not established.

[![Feature quality](https://github.com/Vinay-711/mplads-sentinel-sih-2026/actions/workflows/quality.yml/badge.svg)](https://github.com/Vinay-711/mplads-sentinel-sih-2026/actions/workflows/quality.yml)

## Reproduce the feature checks

From a fresh clone, use Python 3.11 or 3.14:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements-test.txt
python -m pytest features/tests -q
```

The feature suite checks date/duration calculations, financial ratios, progress gaps,
category benchmarks, raw-data preservation and index alignment. It uses synthetic
fixtures and the checked-in cleaned CSVs; no database, credentials, model downloads
or network calls are needed after installation. GitHub Actions runs this same command
on pull requests and pushes to `main` on both Python versions.

This workflow does **not** run the PostgreSQL-backed API/risk integration suite or
validate deployment, source authenticity, model accuracy or real-world impact.
See [backend setup](backend/README.md) for the database-dependent application.
Historical validation tables below describe prior recorded runs, not guarantees
about a new environment; rerun the relevant commands before relying on them.

## Data and interpretation boundaries

The repository includes [sample project generation](data/scripts/generate_sample_projects.py)
as well as source-ingestion scripts and provenance records. Treat sample project-level
records as demonstration data, not verified findings about real projects or agencies.
Risk indicators support human review; they do not establish fraud or causation.
Check each dataset's provenance and reporting date before any external use.

## Contributing

Use a focused branch and pull request. For calculation changes, include a regression
fixture with expected outputs and run the feature suite above. Preserve raw columns,
project identifiers and row alignment. Never include real credentials or private data.
Document any database-dependent checks separately from offline test results.

---

## 1. Project Overview

This repository provides an end-to-end data acquisition, standardization, auditing, and high-performance database platform for MPLADS governance. Phase 3 establishes a fully normalized, version-controlled PostgreSQL relational database designed for:
- Operational tracking of MPLADS development works (recommendation $\to$ sanction $\to$ work order $\to$ execution $\to$ completion).
- Sub-second full-text and fuzzy search across project titles, sectors, MPs, districts, and agencies.
- Real-time delay detection, budget overrun surveillance, and causal risk factor escalation.
- National and state-level fiscal compliance audits (SC/ST reservation equity, unspent balances, and utilization rates).

---

## 2. Directory Layout

The project follows a modular, production-ready structure:

```
SIH 2026/
├── backend/                                 # Phase 4 FastAPI REST API backend
│   ├── app/
│   │   ├── main.py                          # Application entry point & OpenAPI metadata
│   │   ├── database.py                      # SQLAlchemy session engine & get_db dependency
│   │   ├── models/                          # SQLAlchemy ORM models (exact schema match)
│   │   ├── schemas/                         # Pydantic v2 validation & response DTOs
│   │   ├── routes/                          # FastAPI routers (projects, analytics)
│   │   └── services/                        # Business logic & view querying services
│   ├── tests/test_api.py                    # 17 automated integration tests (100% pass)
│   ├── requirements.txt                     # Backend dependencies
│   ├── .env.example                         # Backend configuration template
│   └── README.md                            # Comprehensive API documentation
├── database/
│   ├── schema.sql                           # Complete idempotent DDL (13 tables, 8 views, 85 indexes)
│   ├── migrate.py                           # Migration engine tracking applied migrations
│   └── migrations/                          # Sequential versioned migration scripts
│       ├── 001_initial_schema.sql           # Dimensions, national summary, calamity, budget
│       ├── 002_project_tracking_schema.sql  # Microdata: projects, financials, progress, risk, history
│       └── 003_search_and_analytics_optimization.sql # FTS TSVECTOR, GIN, pg_trgm, 5 project views
├── scripts/
│   ├── db_config.py                         # Centralized environment-variable connection manager
│   ├── load_to_postgres.py                  # Production loader with topological ordering & upserts
│   ├── validate_database.py                 # Comprehensive 63-check database validation suite
│   └── query_search_examples.py             # 9 query search benchmarks with EXPLAIN plans
├── docs/
│   ├── database_schema.md                   # Complete database catalog, ERD, and column constraints
│   └── database_queries.md                  # Comprehensive search and query optimization guide
├── data/
│   ├── raw/                                 # Untouched raw authoritative source data
│   ├── processed/                           # Standardized Phase 1 intermediate files
│   ├── cleaned/                             # Validated Phase 2 cleaned datasets (CSVs)
│   └── scripts/                             # Phase 1 & 2 acquisition, cleaning, and audit pipeline
├── .env.example                             # Environment variable template (no secrets)
├── .gitignore                               # Excludes .env, caches, and OS artifacts
├── DATABASE_VALIDATION_SUMMARY.md           # Audit scorecard (63/63 checks passed)
└── README.md                                # Project setup and usage documentation
```

---

## 3. PostgreSQL Installation

Ensure PostgreSQL 14+ (PostgreSQL 16 recommended) is installed on your operating system:

### macOS (via Homebrew)
```bash
brew install postgresql@16
brew services start postgresql@16
```

### Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Windows
1. Download the official installer from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/).
2. Run the graphical installer, select PostgreSQL Server and Command Line Tools.
3. Add the PostgreSQL `bin/` directory to your system `PATH`.

### Docker (Alternative Containerized Setup)
```bash
docker run --name mplads-postgres \
  -e POSTGRES_DB=mplads_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -d postgres:16-alpine
```

---

## 4. Database Creation

Create the dedicated project database `mplads_db`:

### Using the Command Line (`createdb`)
```bash
createdb mplads_db
```

### Using `psql`
```sql
CREATE DATABASE mplads_db;
```

### Automated Creation via Python Script
Alternatively, running the automated setup script will create `mplads_db` automatically if it does not already exist:
```bash
python data/scripts/09_setup_database.py
```

---

## 5. Environment Variables Configuration

The database connection strictly reads configuration from environment variables via Python's `python-dotenv`. Credentials are never hardcoded in source code or committed to version control.

### Setup Instructions
1. Copy the template file `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your local PostgreSQL credentials:

```ini
# PostgreSQL Database Configuration for MPLADS Project
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mplads_db
DB_USER=your_postgres_username
DB_PASSWORD=your_secure_password
```

### Configuration Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL server host name or IP address |
| `DB_PORT` | `5432` | Port on which PostgreSQL server listens |
| `DB_NAME` | `mplads_db` | Target database name |
| `DB_USER` | Current OS user / `postgres` | Database role/user for authentication |
| `DB_PASSWORD` | *(empty string)* | Password for the database user |

> [!CAUTION]
> Never commit `.env` containing production passwords to GitHub or version control. Ensure `.env` is listed in `.gitignore`.

---

## 6. Schema Creation & Migrations

The database schema is defined across **13 relational tables**, **8 analytical views**, and **85 performance indexes**.

You can initialize the schema using either the versioned migration runner or the full idempotent DDL script:

### Option A: Run Versioned Migrations (Recommended)
The migration engine tracks applied scripts in the `schema_migrations` table, ensuring safe, repeatable execution:
```bash
python database/migrate.py
```

The migration runner applies:
1. `database/migrations/001_initial_schema.sql` – Dimensions (`states`, `constituencies`), macro summaries, calamity relief, budget series, and state expenditure.
2. `database/migrations/002_project_tracking_schema.sql` – Project tracking tables (`projects`, `financials`, `progress`, `risk_scores`, `risk_factors`, `project_history`).
3. `database/migrations/003_search_and_analytics_optimization.sql` – `pg_trgm` extension, Full-Text Search `search_vector`, GIN indexes, and 5 operational project views.

### Option B: Execute Full Schema DDL via `psql`
```bash
psql -h localhost -p 5432 -U your_postgres_username -d mplads_db -f database/schema.sql
```

---

## 7. Data Loading

Load the Phase 2 validated dataset into PostgreSQL using the production-ready loader:

```bash
python scripts/load_to_postgres.py
```

### Ingestion Features
- **Strict Topological Dependency Order**: Dimensions and master entities (`states`, `constituencies`) are loaded first, followed by `projects`, followed by child tables (`financials`, `progress`, `risk_scores`, `risk_factors`, `project_history`).
- **Data Type Casting & Integrity**: Cleansed strings, integers, numerics, and ISO-8601 dates (`YYYY-MM-DD`) are properly cast into native PostgreSQL types.
- **Controlled SQL NULL Preservation**: Pandas `NaN`/`NA` values are converted to genuine SQL `NULL`s, preserving legitimate data boundaries without arbitrary zero-filling.
- **Idempotent Upsert Strategy**: Uses `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING` to ensure safe re-execution without duplicate key errors.
- **Transaction Safety**: Batched operations execute within transactions; any critical failure triggers an immediate rollback.
- **Transparent Logging**: Reports processed, inserted/updated, skipped, and failed record counts.

---

## 8. Database Validation

Run the comprehensive, read-only validation suite to verify the database integrity:

```bash
python scripts/validate_database.py
```

The validator performs **63 distinct audit checks** across 9 categories and exits with code `0` on success (or code `1` on critical failure):

```
================================================================================
                    MPLADS DATABASE VALIDATION SCORECARD
================================================================================
  Category                                            Passed  Failed     Rate
--------------------------------------------------------------------------------
  1. Row Count & Table Existence Checks                   13       0   100.0%
  2. Project Completeness & Foreign Key Integrity         12       0   100.0%
  3. Unique Constraint & Deduplication Checks              6       0   100.0%
  4. Mandatory Field NOT NULL Checks                      10       0   100.0%
  5. Date Validity & Chronological Sequence Checks         5       0   100.0%
  6. Financial Math & Balance Consistency Checks           5       0   100.0%
  7. Prohibited & Boundary Value Checks                    6       0   100.0%
  8. Legitimate SQL NULL Preservation Checks               3       0   100.0%
  9. Operational & Analytical Views Functionality          3       0   100.0%
--------------------------------------------------------------------------------
  TOTAL CHECKS                                            63       0   100.0%
================================================================================
```

A detailed audit report is automatically generated at `DATABASE_VALIDATION_SUMMARY.md`.

---

## 9. Searching and Querying the Database

### Search Architecture & Indexes
- **Full-Text Search (FTS)**: `projects.search_vector` (`TSVECTOR`) indexed with GIN index `idx_projects_search_vector`.
- **Fuzzy Trigram Matching**: `pg_trgm` GIN indexes on `project_title`, `mp_name`, `implementing_agency`, and `district_name`.
- **Composite B-Tree Indexes**: Optimized for multi-field queries: `(state_id, district_name)`, `(current_status, sector)`.

### Example Queries

#### 1. Search by Project ID
```sql
SELECT 
    p.project_id, p.project_code, p.project_title, p.sector,
    s.state_name, p.district_name, p.mp_name, p.current_status,
    f.sanctioned_amount, f.expenditure_amount
FROM projects p
JOIN states s ON p.state_id = s.state_id
JOIN financials f ON p.project_id = f.project_id
WHERE p.project_id = 'MPLADS-2024-0001';
```

#### 2. Search by State & District
```sql
SELECT 
    p.project_id, p.project_title, p.sector, p.current_status,
    f.sanctioned_amount, pr.physical_progress_pct
FROM projects p
JOIN financials f ON p.project_id = f.project_id
LEFT JOIN progress pr ON p.project_id = pr.project_id
WHERE p.state_id = 10 AND p.district_name = 'Patna';
```

#### 3. Full-Text Natural Language Search
```sql
SELECT 
    p.project_id, p.project_title, p.sector, s.state_name, p.district_name,
    ROUND(ts_rank(p.search_vector, websearch_to_tsquery('english', 'Solar OR RO Water'))::NUMERIC, 4) AS rank
FROM projects p
JOIN states s ON p.state_id = s.state_id
WHERE p.search_vector @@ websearch_to_tsquery('english', 'Solar OR RO Water')
ORDER BY rank DESC;
```

#### 4. Find Delayed & Stalled Projects (Operational View)
```sql
SELECT 
    project_id, project_title, state_name, district_name,
    implementing_agency, days_delayed, milestone_status, delay_risk_score
FROM v_delayed_projects;
```

#### 5. Find High-Risk Projects with Contributing Factors
```sql
SELECT 
    project_id, project_title, state_name, overall_risk_score,
    risk_level, primary_risk_factors
FROM v_high_risk_projects;
```

#### 6. Typo-Tolerant MP Name Matching (`pg_trgm`)
```sql
SELECT 
    p.project_id, p.project_title, p.mp_name, s.state_name,
    ROUND(similarity(p.mp_name, 'Kumar')::NUMERIC, 3) AS similarity_score
FROM projects p
JOIN states s ON p.state_id = s.state_id
WHERE p.mp_name % 'Kumar' OR p.mp_name ILIKE '%Kumar%'
ORDER BY similarity_score DESC
LIMIT 5;
```

### Running the Query Benchmark Suite
To execute all 9 query benchmarks with `EXPLAIN` query plans:
```bash
python scripts/query_search_examples.py
```

For the complete query catalog, refer to [docs/database_queries.md](docs/database_queries.md).

---

## 10. Master Pipeline Execution

To run the complete data pipeline from raw data acquisition through database loading and validation:

```bash
python data/scripts/run_all.py
```

This single orchestrator runs:
1. `01_download_esakshi_master.py` – Acquires official e-Sakshi dimensions (States & Constituencies).
2. `02_download_union_budget.py` – Ingests 33-year Union Budget Demand No. 91 series.
3. `03_download_parliament_qa.py` – Ingests audited Parliament QA expenditure data.
4. `04_process_and_standardize.py` – Standardizes schemas, column names, and keys.
5. `05_profile_datasets.py` – Analyzes data types, distributions, and missingness.
6. `clean_mplads_data.py` – Cleans and normalizes datasets, applies constraints.
7. `07_validate_cleaned_data.py` – Performs Phase 2 data-quality validation.
8. `08_audit_phase2.py` – Final Phase 2 data audit.
9. `09_setup_database.py` – Provisions PostgreSQL `mplads_db` and applies DDL schema.
10. `load_to_postgres.py` – Loads all 13 tables in topological order with upserts.
11. `11_verify_database.py` – Runs 96 technical verification checks.
12. `validate_database.py` – Executes the comprehensive 63-check validation suite.

---

## 11. Security & Compliance Notes
- No cleartext passwords or secrets are committed to this repository.
- Local configuration is managed strictly via `.env` (git-ignored).
- All SQL views and scripts use parameterized queries to prevent SQL injection vulnerabilities.
