# LedgerForge

LedgerForge is a layered FastAPI service for employee and payroll operations. This repository contains Phase 1 foundations and Phase 2 attendance, leave, payroll, payslip, accounting, and invoice workflows.

Local project path (PowerShell):

```powershell
cd C:\Users\mikki\Documents\LedgerForge_Phase1_Submission
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

The tests cover health, CRUD, duplicate email constraint behavior, pagination with search and department filtering, direct reports, department employees, shared API errors, Phase 2 attendance and leave rules, payroll calculations, payslip authorization, journal posting/reversal, and invoice lifecycle behavior.

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

## Phase 2 workflows

Phase 2 extends the schema through Alembic and loads the provided master and transaction CSVs. Attendance imports in chunks of 5,000 rows. Payroll output is calculated by the application engine from employee, salary, attendance, statutory, and tax inputs; `data/master/payroll_items.csv` is retained only as the supplied answer key for comparison and is not loaded as calculation input.

Run migrations and load the full dataset:

```powershell
cd C:\Users\mikki\Documents\LedgerForge_Phase1_Submission
python -m alembic upgrade head
python -m scripts.seed
```

Useful Phase 2 routes include:

- `GET /attendance/summary/{employee_id}?year=2025&month=4`
- `POST /leave-requests`, `POST /leave-requests/{id}/approve`, `POST /leave-requests/{id}/reject`
- `GET /payslips/{employee_id}/{run_id}` (PDF; send `X-User-Id` for the requesting employee or an HR user)
- `GET /accounting/accounts/{account_code}/balance`, `POST /accounting/journal-entries/{id}/reverse`
- Invoice draft, cancellation, posting, payment, and receivables routes under `/invoices`

For API details, use `http://localhost:8000/docs`. The `X-User-Id` header is a demonstration identity mechanism for this learning project, not production authentication. Use the documented examples and tests to see request shapes.

Run the focused Phase 2 checks:

```powershell
python -m pytest
python -m scripts.attendance_hand_check
python -m scripts.calculate_payroll
python scripts/verify_ledgerforge.py checks --data data/master
python scripts/verify_ledgerforge.py payroll exports/payroll_run.csv --data data/master
python -m scripts.diagnose_payroll
```

The mini-challenge walkthrough and evidence files are in `docs/phase2_evidence/`. Payroll accuracy is evaluated separately against the supplied expected-answer CSV. The current engine does not meet the stated 99% target (see the Phase 2 report and `exports/payroll_mismatch_log.csv`); the provided materials do not specify the variable-pay and tax calculation policies needed to resolve all differences. Do not describe this payroll accuracy result as passing.

## Phase 2 evidence and report

`docs/phase2_evidence/` contains attendance CSV/API hand checks, generated sample payslips and comparison results, and the mini-challenge walkthrough. The final report is `output/pdf/Python_MILIND_KUMAR_Phase2_Report.pdf`.
