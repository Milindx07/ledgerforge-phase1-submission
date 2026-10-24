# LedgerForge Phase 1 Project Opening Guide

## Project Folder

Use this project folder on your machine:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
```

## Start the Application

```powershell
cd C:\Users\mikki\Documents\LedgerForge
copy .env.example .env
docker compose up --build
```

When the terminal shows that Uvicorn is running, open:

```text
http://localhost:8000/docs
```

Health check:

```powershell
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run Tests

If Docker is running:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
docker compose exec api pytest
```

Local Python option:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
```

## Run Migrations

```powershell
cd C:\Users\mikki\Documents\LedgerForge
docker compose exec api alembic upgrade head
```

Rollback check:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
docker compose exec api alembic downgrade base
docker compose exec api alembic upgrade head
```

## Seed the Dataset

Quick seed check:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
docker compose exec api python -m scripts.seed --attendance-limit 1000
```

Full seed:

```powershell
cd C:\Users\mikki\Documents\LedgerForge
docker compose exec api python -m scripts.seed
```

The seed can be run more than once. It updates existing rows instead of creating duplicates.

## Important Files for Review

```text
README.md
PHASE1_TASKS_SUMMARY.md
PROJECT_OPENING_GUIDE.md
docs/api_contract.md
docs/openapi.json
docs/er_diagram.md
docs/dataset_notes.md
data/sample/day2_employees.csv
data/sample/day2_employees.json
exports/employees.csv
exports/salaries.csv
exports/salary_structures.csv
exports/attendance.csv
```

The folder is also initialized as a local Git repository. `.env` is ignored and is not part of the committed files.

## Verification Completed

The following checks were completed:

```powershell
pytest
ruff check .
alembic upgrade head
python -m scripts.seed --attendance-limit 1000
python -m scripts.seed --attendance-limit 1000
```

Result:

- Tests passed: 9
- Lint passed
- Migrations applied
- Seed ran twice without duplicates
- Employee export includes generated phone numbers
- Salary and attendance exports open correctly
