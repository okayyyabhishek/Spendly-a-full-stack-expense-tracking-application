# Spendly

Spendly is a full-stack personal expense tracker built from the supplied product requirements. It uses a React + TypeScript + Vite frontend, FastAPI + SQLAlchemy backend, and MySQL database. All finance data is user-scoped and persisted through REST APIs - the web app does not use fabricated financial figures.

## Requirements traceability

The 21-page product specification has been fully reviewed. It requires secure registration/login; transaction, category, budget, recurring transaction, reporting/export, analytics, notification, and monthly summary modules; responsive fintech UI; API pagination/filtering; database constraints/indexes; no fake data; error/loading/empty states; documentation; seed data only for explicit development/demo use; and critical backend test coverage.

The project will be completed in the requested order:

1. Architecture, configuration, database runtime, and quality baseline.
2. Normalized database models and migrations.
3. Authentication and user isolation.
4. REST APIs.
5. Frontend system and connected feature modules (auth, dashboard, transactions/categories/history/search, budgets, recurring payments, analytics, notifications, exports).
6. Mobile, error/loading states, tests, and final integration.

## Structure

```text
backend/
  app/
    api/          # HTTP routers
    core/         # configuration, security, errors
    database/     # SQLAlchemy session and migration wiring
    models/       # relational entities
    schemas/      # Pydantic request and response models
    services/     # domain logic and report generation
  tests/
frontend/
  src/
    api/          # typed API client
    components/   # reusable UI primitives
    features/     # feature-specific UI and state
    layouts/ pages/ hooks/ types/
infra/mysql/      # MySQL initialization assets
```

## Implemented features

The project now includes the complete requested feature set: JWT registration/login/logout and user isolation; default and custom categories; live income/expense CRUD; server-side transaction search, date/category/type/payment/amount filters, and pagination; overall and category budgets with warnings; recurring schedules that materialize transactions automatically; dashboard, category, time-series, financial metrics, and monthly summaries; notification center; CSV/PDF exports; loading, error, empty, and confirmation states; desktop/mobile layouts; and backend critical-flow tests.

No financial figure in the frontend is hardcoded. Cards, charts, history, budget progress, alerts, and exports all request the authenticated FastAPI API and use database records.

## Local setup

Prerequisites: Python 3.11+, Node.js 20+, pnpm, and Docker Desktop.

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make database-up
make backend-install
make frontend-install
make backend-migrate
make backend-run
```

In a second terminal:

```bash
make frontend-run
```

Open the frontend at `http://localhost:5173`; OpenAPI documentation is at `http://localhost:8000/api/v1/docs`.

Run the current backend baseline with:

```bash
make backend-test
```

## Migrations and optional demo data

Apply any schema change with:

```bash
make backend-migrate
```

An optional development-only seed creates a demo account and the PDF's requested realistic sample transactions. It never replaces normal database behavior and refuses to run in production:

```bash
SEED_PASSWORD='ChooseAStrongPassword9' make backend-seed
```

To use the API without the web application, inspect the authenticated OpenAPI routes at `http://localhost:8000/api/v1/docs`.

Do not commit `.env` files. Replace all local placeholder secrets before deploying.
