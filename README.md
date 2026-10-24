# LedgerForge Phase 1

LedgerForge is a layered FastAPI service for the first four Phase 1 tasks: project skeleton, employee data model, CRUD APIs, and repeatable master-data seeding.

Local project path:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
```

## What is included

- Layered FastAPI app: routes, services, schemas, models, and settings.
- `/health` endpoint returning `{"status": "ok"}`.
- Environment-based settings with `.env.example`.
- Dockerfile and Docker Compose with `api` and PostgreSQL `db` services.
- SQLAlchemy models for departments, roles, employees, manager hierarchy, assignments, salary structures, and attendance.
- Alembic migration with rollback support.
- Employee CRUD, team, and department endpoints with pagination, filtering, search, validation, soft delete, and one error format.
- Seed script and CSV exports from the supplied master dataset.
- API contract, ER diagram, tests, and sample Day-2 data.

## Setup

```bash
cd LedgerForge
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Run with Docker

```bash
cd LedgerForge
docker compose up --build
```

Open:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Migrations

```bash
cd LedgerForge
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic downgrade base
```

## Tests

```bash
cd LedgerForge
pytest
```

The tests cover health, CRUD, duplicate email constraint behavior, pagination with search and department filtering, direct reports, department employees, and shared API error format.

## Seed and exports

The repository includes workbook-derived CSVs under `data/master`.

```bash
cd LedgerForge
python -m scripts.seed
```

For a quick local trial with only a small attendance slice:

```bash
cd LedgerForge
python -m scripts.seed --attendance-limit 1000
```

The seed is safe to run more than once. It uses primary keys to update existing rows instead of inserting duplicates. It also writes CSV exports for:

- `exports/employees.csv`
- `exports/salaries.csv`
- `exports/salary_structures.csv`
- `exports/attendance.csv`

To regenerate CSVs from the workbook:

```bash
cd LedgerForge
python -m scripts.seed --source-xlsx data/raw/01_LedgerForge_Python_Master_Dataset.xlsx
```

## Role design decision

For Phase 1, an employee has one current role through `employees.role_id`, plus a full historical record in `employee_assignments`. This keeps Task 3 CRUD simple and gives payroll/reporting a clear current role. If the product later needs simultaneous roles, `employee_assignments` can become the source for multiple active assignments without changing employee identity.

## Data source

The supplied workbook is fictional training data for Zenith Nova Technologies. It says all people, companies, emails, and numbers are generated for learning. No real secrets or passwords are stored. The assignment asks for Kaggle license tracking; because the supplied workbook has no separate public license, the current notes document it as a provided training source in `docs/dataset_notes.md`.

## Project layout

```text
LedgerForge/
  app/
    api/routes/
    core/
    models/
    schemas/
    services/
  alembic/
  data/
    master/
    sample/
  docs/
  scripts/
  tests/
```
