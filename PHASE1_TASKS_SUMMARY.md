# Phase 1 Project Summary

Project: LedgerForge Python API

## Task 1. Skeleton and Handoff

Completed:

- Created a layered FastAPI app with `app/api/routes`, `app/services`, `app/schemas`, `app/models`, and `app/core`.
- Initialized the project as a local Git repository with an initial commit.
- Added environment-based settings using `pydantic-settings`.
- Added `.env.example` without real secrets.
- Added `/health`, which returns `{"status": "ok"}`.
- Added Dockerfile and Docker Compose with `api` and PostgreSQL `db`.
- Added pytest health test.
- Added draft API contract in `docs/api_contract.md`.
- Added OpenAPI export in `docs/openapi.json`.
- Added Day-2 sample data in `data/sample/day2_employees.csv` and `data/sample/day2_employees.json`.

Commands:

```bash
cd LedgerForge
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000/docs` for the automatic API page.

## Task 2. Employee Data Model

Completed:

- Added SQLAlchemy models for departments, roles, employees, employee assignments, salary structures, and attendance.
- Added employee manager hierarchy through `employees.manager_id`.
- Added `created_at`, `updated_at`, and `is_active` for soft delete.
- Added unique constraint on `work_email`.
- Added indexes for employee name, manager, email, and department lookup.
- Added Alembic migration with upgrade and downgrade.
- Added ER diagram in `docs/er_diagram.md`.
- Wrote tests proving duplicate email fails.

Design decision:

An employee has one current role in `employees.role_id`, with role history tracked in `employee_assignments`. This keeps the API simple while preserving assignment history.

Commands:

```bash
cd LedgerForge
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic downgrade base
docker compose run --rm api alembic upgrade head
```

## Task 3. Employee and Team APIs

Completed:

- Added `POST /employees`.
- Added `GET /employees`.
- Added `GET /employees/{employee_id}`.
- Added `PATCH /employees/{employee_id}`.
- Added `DELETE /employees/{employee_id}` as soft delete.
- Added `GET /departments`.
- Added `GET /departments/{department_id}/employees`.
- Added `GET /employees/{employee_id}/team` for direct reports.
- Added pagination with `page` and `size`.
- Added department filtering and search with `department` and `q`.
- Added validation for email, non-empty names, and future joining date.
- Added one consistent error format.
- Kept business logic in services, not routes.
- Added tests for successful endpoints and bad input.

Example:

```bash
cd LedgerForge
pytest
```

## Task 4. Master Dataset and Seed

Completed:

- Converted the supplied master workbook into CSV files under `data/master`.
- Used the task mapping from the workbook README:
  - Task 1: first 10 employees plus departments.
  - Task 2: departments, roles, employees, employee assignments.
  - Task 3: employees, departments, employee assignments.
  - Task 4: workbook-derived seed and CSV export targets.
- Added repeatable seed command in `scripts/seed.py`.
- Used primary-key upserts so running the seed twice does not create duplicates.
- Added fixed Faker seed for fallback generated values.
- Generated deterministic employee phone numbers during seed when the source does not provide them.
- Added exports for employees, salaries, salary structures, and attendance under `exports`.
- Added dataset notes in `docs/dataset_notes.md`.

Commands:

```bash
cd LedgerForge
python -m scripts.seed
```

Quick local check:

```bash
cd LedgerForge
python -m scripts.seed --attendance-limit 1000
```

## Verification Performed

```bash
cd LedgerForge
pytest
ruff check .
alembic upgrade head
alembic downgrade base
python -m scripts.seed --attendance-limit 1000
```

Result:

- `pytest`: 9 passed.
- `ruff check .`: all checks passed.
- Alembic upgrade and downgrade both completed.
- Seed command completed and produced CSV exports.
