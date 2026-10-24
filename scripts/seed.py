from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from faker import Faker
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import (
    Attendance,
    Base,
    Department,
    Employee,
    EmployeeAssignment,
    Role,
    SalaryStructure,
)

FAKER_SEED = 20261013
DEFAULT_DATA_DIR = Path("data/master")
DEFAULT_EXPORT_DIR = Path("exports")
EXPORT_TARGETS = ("employees", "salary_structures", "salaries", "attendance")
LOAD_ORDER = (
    "departments",
    "roles",
    "employees",
    "employee_assignments",
    "salary_structures",
    "attendance",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed LedgerForge from workbook-derived CSV files."
    )
    parser.add_argument(
        "--source-xlsx",
        type=Path,
        help="Optional master workbook to convert into CSVs.",
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument(
        "--attendance-limit",
        type=int,
        default=0,
        help="Optional row limit for attendance during quick local testing. 0 loads all rows.",
    )
    return parser.parse_args()


def normalize_date(value: Any) -> Any:
    if pd.isna(value) or value == "":
        return None
    return pd.to_datetime(value).date()


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def export_workbook_to_csv(source_xlsx: Path, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    workbook = pd.ExcelFile(source_xlsx)
    for sheet in workbook.sheet_names:
        frame = workbook.parse(sheet)
        frame.to_csv(data_dir / f"{sheet}.csv", index=False)


def read_csv(data_dir: Path, name: str, limit: int = 0) -> pd.DataFrame:
    path = data_dir / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing required seed file: {path}")
    return pd.read_csv(path, nrows=limit if limit > 0 else None)


def upsert_departments(db: Session, frame: pd.DataFrame) -> None:
    for row in frame.to_dict("records"):
        db.merge(
            Department(
                department_id=str(row["department_id"]),
                department_name=str(row["department_name"]),
                cost_center=str(row["cost_center"]),
                description=clean_value(row.get("description")),
            )
        )


def upsert_roles(db: Session, frame: pd.DataFrame) -> None:
    for row in frame.to_dict("records"):
        db.merge(
            Role(
                role_id=str(row["role_id"]),
                department_id=str(row["department_id"]),
                role_title=str(row["role_title"]),
                level=int(row["level"]),
                grade=str(row["grade"]),
                band_min_annual=clean_value(row["band_min_annual"]),
                band_mid_annual=clean_value(row["band_mid_annual"]),
                band_max_annual=clean_value(row["band_max_annual"]),
                overtime_eligible=str(row["overtime_eligible"]).upper() == "Y",
                band_year=int(row["band_year"]),
            )
        )


def upsert_employees(db: Session, frame: pd.DataFrame) -> None:
    fake = Faker("en_IN")
    Faker.seed(FAKER_SEED)
    manager_links: dict[str, str | None] = {}

    for idx, row in enumerate(frame.to_dict("records"), start=1):
        first_name = clean_value(row.get("first_name")) or fake.first_name()
        last_name = clean_value(row.get("last_name")) or fake.last_name()
        full_name = clean_value(row.get("full_name")) or f"{first_name} {last_name}"
        email = clean_value(row.get("work_email")) or fake.unique.company_email()
        phone_number = clean_value(row.get("phone_number")) or f"+91-90000-{idx:05d}"
        status = clean_value(row.get("employment_status")) or "Active"
        employee_id = str(row["employee_id"])
        manager_links[employee_id] = clean_value(row.get("manager_id"))

        db.merge(
            Employee(
                employee_id=employee_id,
                first_name=str(first_name),
                last_name=str(last_name),
                full_name=str(full_name),
                work_email=str(email).lower(),
                gender=clean_value(row.get("gender")),
                date_of_birth=normalize_date(row.get("date_of_birth")),
                hire_date=normalize_date(row.get("hire_date")),
                exit_date=normalize_date(row.get("exit_date")),
                employment_status=str(status),
                employment_type=clean_value(row.get("employment_type")),
                department_id=clean_value(row.get("department_id")),
                role_id=clean_value(row.get("role_id")),
                manager_id=None,
                phone_number=phone_number,
                work_location=clean_value(row.get("work_location")),
                work_mode=clean_value(row.get("work_mode")),
                highest_education=clean_value(row.get("highest_education")),
                is_active=str(status).lower() == "active",
            )
        )

    db.flush()
    existing_employee_ids = {
        employee_id for (employee_id,) in db.query(Employee.employee_id).all()
    }
    for employee_id, manager_id in manager_links.items():
        employee = db.get(Employee, employee_id)
        if employee is not None:
            employee.manager_id = manager_id if manager_id in existing_employee_ids else None


def upsert_assignments(db: Session, frame: pd.DataFrame) -> None:
    for row in frame.to_dict("records"):
        db.merge(
            EmployeeAssignment(
                assignment_id=str(row["assignment_id"]),
                employee_id=str(row["employee_id"]),
                effective_from=normalize_date(row.get("effective_from")),
                effective_to=normalize_date(row.get("effective_to")),
                department_id=str(row["department_id"]),
                role_id=str(row["role_id"]),
                job_level=int(row["job_level"]),
                manager_id=clean_value(row.get("manager_id")),
                change_reason=str(row["change_reason"]),
            )
        )


def upsert_salary_structures(db: Session, frame: pd.DataFrame) -> None:
    for row in frame.to_dict("records"):
        db.merge(
            SalaryStructure(
                structure_id=str(row["structure_id"]),
                employee_id=str(row["employee_id"]),
                component_id=str(row["component_id"]),
                component_name=str(row["component_name"]),
                component_type=str(row["component_type"]),
                monthly_amount=clean_value(row["monthly_amount"]),
                effective_from=normalize_date(row.get("effective_from")),
                effective_to=normalize_date(row.get("effective_to")),
                revision_id=str(row["revision_id"]),
            )
        )


def upsert_attendance(db: Session, frame: pd.DataFrame) -> None:
    for row in frame.to_dict("records"):
        db.merge(
            Attendance(
                attendance_id=str(row["attendance_id"]),
                employee_id=str(row["employee_id"]),
                attendance_date=normalize_date(row.get("attendance_date")),
                weekday=str(row["weekday"]),
                status=str(row["status"]),
                leave_type_code=clean_value(row.get("leave_type_code")),
                check_in=clean_value(row.get("check_in")),
                check_out=clean_value(row.get("check_out")),
                hours_worked=clean_value(row.get("hours_worked")),
                overtime_hours=clean_value(row.get("overtime_hours")),
                late_flag=clean_value(row.get("late_flag")),
                source=clean_value(row.get("source")),
                data_quality_flag=clean_value(row.get("data_quality_flag")),
                department_id=clean_value(row.get("department_id")),
            )
        )


LOADERS = {
    "departments": upsert_departments,
    "roles": upsert_roles,
    "employees": upsert_employees,
    "employee_assignments": upsert_assignments,
    "salary_structures": upsert_salary_structures,
    "attendance": upsert_attendance,
}


def export_targets(data_dir: Path, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPORT_TARGETS:
        source_name = "salary_structures" if name == "salaries" else name
        source = data_dir / f"{source_name}.csv"
        if source.exists():
            frame = pd.read_csv(source)
            if name == "employees" and "phone_number" not in frame.columns:
                frame["phone_number"] = [
                    f"+91-90000-{idx:05d}" for idx in range(1, len(frame) + 1)
                ]
            frame.to_csv(export_dir / f"{name}.csv", index=False)


def main() -> None:
    args = parse_args()
    if args.source_xlsx:
        export_workbook_to_csv(args.source_xlsx, args.data_dir)

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for name in LOAD_ORDER:
            limit = args.attendance_limit if name == "attendance" else 0
            frame = read_csv(args.data_dir, name, limit=limit)
            LOADERS[name](db, frame)
            db.commit()

    export_targets(args.data_dir, args.export_dir)
    print(
        "Seed complete. Re-running this command updates existing rows instead of duplicating them."
    )


if __name__ == "__main__":
    main()
