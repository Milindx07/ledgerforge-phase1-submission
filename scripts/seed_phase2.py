from __future__ import annotations

import argparse
import csv
import time
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, delete, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import (
    Attendance,
    Base,
    ChartOfAccount,
    Client,
    Department,
    Employee,
    EmployeeAssignment,
    Holiday,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    JournalEntry,
    JournalLine,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    PayrollItem,
    PayrollRun,
    PerformanceReview,
    Role,
    SalaryComponent,
    SalaryRevision,
    SalaryStructure,
    StatutoryRate,
    TaxParameter,
    TaxSlab,
    User,
)
from scripts.calculate_payroll import calculate as calculate_payroll

DEFAULT_DATA_DIR = Path("data/master")
DEFAULT_EXPORT_DIR = Path("exports/seeded")
CHUNK_SIZE = 5000

LOAD_ORDER: tuple[tuple[str, type[Base]], ...] = (
    ("departments", Department),
    ("roles", Role),
    ("employees", Employee),
    ("employee_assignments", EmployeeAssignment),
    ("salary_components", SalaryComponent),
    ("salary_revisions", SalaryRevision),
    ("salary_structures", SalaryStructure),
    ("performance_reviews", PerformanceReview),
    ("holidays", Holiday),
    ("leave_types", LeaveType),
    ("leave_requests", LeaveRequest),
    ("leave_balances", LeaveBalance),
    ("attendance", Attendance),
    ("statutory_rates", StatutoryRate),
    ("tax_slabs", TaxSlab),
    ("tax_parameters", TaxParameter),
    ("users", User),
    ("payroll_runs", PayrollRun),
    ("chart_of_accounts", ChartOfAccount),
    ("clients", Client),
    ("invoices", Invoice),
    ("invoice_items", InvoiceItem),
    ("invoice_payments", InvoicePayment),
    ("journal_entries", JournalEntry),
    ("journal_lines", JournalLine),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load LedgerForge's Phase 1 and Phase 2 training CSV data."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--attendance-chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument(
        "--attendance-limit",
        type=int,
        default=0,
        help="Optional attendance row cap for a quick local trial; 0 loads all rows.",
    )
    return parser.parse_args()


def _empty(value: Any) -> bool:
    return value is None or (
        isinstance(value, str)
        and value.strip().lower() in {"", "nan", "none", "null"}
    )


def _as_bool(value: Any) -> bool | None:
    if _empty(value):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() in {"Y", "YES", "TRUE", "1", "ACTIVE"}


def _convert(value: Any, column_type: Any) -> Any:
    if _empty(value):
        return None
    if isinstance(column_type, Boolean):
        return _as_bool(value)
    if isinstance(column_type, DateTime):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    if isinstance(column_type, Date):
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        return date.fromisoformat(str(value)[:10])
    if isinstance(column_type, Numeric):
        return Decimal(str(value).replace(",", ""))
    if isinstance(column_type, Integer):
        return int(Decimal(str(value)))
    return str(value).strip()


def _record(model: type[Base], raw: dict[str, Any], row_number: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name in raw:
            result[column.name] = _convert(raw[column.name], column.type)

    if model is Employee:
        result["is_active"] = (result.get("employment_status") or "").lower() == "active"
        if result.get("phone_number") is None:
            result["phone_number"] = f"+91-90000-{row_number:05d}"
    elif model is LeaveRequest:
        result["status"] = (result.get("status") or "PENDING").upper().replace(" ", "_")
    elif model is PayrollRun:
        result["status"] = (result.get("status") or "DRAFT").upper().replace(" ", "_")
    elif model is JournalEntry:
        result["status"] = (result.get("status") or "POSTED").upper()
    elif model is Invoice:
        result["status"] = (result.get("status") or "DRAFT").upper().replace(" ", "_")
        result["status"] = {
            "PARTIALLYPAID": "PARTIALLY_PAID",
            "PARTIALLY-PAID": "PARTIALLY_PAID",
        }.get(result["status"], result["status"])
    elif model is ChartOfAccount and result.get("parent_code"):
        result["parent_code"] = str(result["parent_code"]).removesuffix(".0")
    return result


def _batches(path: Path, chunk_size: int):
    if not path.exists():
        raise FileNotFoundError(f"Missing required seed file: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        batch: list[dict[str, Any]] = []
        for row_number, raw in enumerate(reader, start=1):
            batch.append(raw)
            if len(batch) >= chunk_size:
                yield row_number - len(batch) + 1, batch
                batch = []
        if batch:
            yield row_number - len(batch) + 1, batch


def _source_batches(
    name: str,
    model: type[Base],
    data_dir: Path,
    chunk_size: int,
    attendance_limit: int,
):
    path = data_dir / f"{name}.csv"
    if name == "leave_balances":
        for start, rows in _batches(path, chunk_size):
            output: list[dict[str, Any]] = []
            for raw in rows:
                common = {
                    "employee_id": str(raw["employee_id"]),
                    "financial_year": str(raw["financial_year"]),
                    "as_of_date": _convert(raw["as_of_date"], Date()),
                }
                for code, entitlement, used, balance in (
                    ("CL", "cl_entitlement", "cl_used", "cl_balance"),
                    ("SL", "sl_entitlement", "sl_used", "sl_balance"),
                    ("EL", None, "el_used_fy", "el_balance"),
                ):
                    used_value = Decimal(str(raw.get(used) or 0))
                    balance_value = Decimal(str(raw.get(balance) or 0))
                    entitlement_value = (
                        Decimal(str(raw[entitlement])) if entitlement else used_value + balance_value
                    )
                    output.append(
                        {
                            **common,
                            "leave_type_code": code,
                            "entitlement_days": entitlement_value,
                            "used_days": used_value,
                            "balance_days": balance_value,
                            "pending_days": Decimal("0"),
                        }
                    )
            yield output
        return

    count = 0
    for start, rows in _batches(path, chunk_size):
        output = [_record(model, row, start + offset) for offset, row in enumerate(rows)]
        if name == "attendance" and attendance_limit > 0:
            remaining = attendance_limit - count
            if remaining <= 0:
                break
            output = output[:remaining]
        yield output
        count += len(output)
        if name == "attendance" and attendance_limit > 0 and count >= attendance_limit:
            break


def _upsert(db: Session, model: type[Base], records: list[dict[str, Any]]) -> None:
    if not records:
        return
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        stmt = sqlite_insert(model)
    elif dialect == "postgresql":
        stmt = postgres_insert(model)
    else:
        raise RuntimeError(f"Bulk idempotent seed does not support database dialect {dialect!r}")
    pk_columns = [column.name for column in model.__table__.primary_key.columns]
    update_columns = {
        column.name: getattr(stmt.excluded, column.name)
        for column in model.__table__.columns
        if column.name not in pk_columns
    }
    db.execute(
        stmt.on_conflict_do_update(index_elements=pk_columns, set_=update_columns), records
    )


def _seed_missing_leave_balances(db: Session) -> None:
    """The supplied snapshot tracks CL/SL/EL; initialize ML/BL from policy quotas."""
    types = {row.leave_type_code: row for row in db.scalars(select(LeaveType)).all()}
    eligible_types = [types[c] for c in ("ML", "BL") if c in types]
    if not eligible_types:
        return
    existing = {
        (row.employee_id, row.leave_type_code, row.financial_year)
        for row in db.scalars(select(LeaveBalance)).all()
    }
    approved = defaultdict(Decimal)
    tracked_codes = {item.leave_type_code for item in eligible_types}
    for leave in db.scalars(select(LeaveRequest).where(LeaveRequest.status == "APPROVED")):
        if leave.leave_type_code in tracked_codes and leave.start_date.year == 2026:
            key = (leave.employee_id, leave.leave_type_code)
            approved[key] += Decimal(str(leave.days))

    employees = db.scalars(select(Employee).where(Employee.is_active.is_(True))).all()
    new_rows = []
    for employee in employees:
        for leave_type in eligible_types:
            financial_year = "FY2026-27"
            key = (employee.employee_id, leave_type.leave_type_code, financial_year)
            if key in existing:
                continue
            used = approved[(employee.employee_id, leave_type.leave_type_code)]
            quota = Decimal(str(leave_type.annual_quota_days))
            new_rows.append(
                LeaveBalance(
                    employee_id=employee.employee_id,
                    leave_type_code=leave_type.leave_type_code,
                    financial_year=financial_year,
                    as_of_date=date(2026, 9, 30),
                    entitlement_days=quota,
                    used_days=used,
                    balance_days=max(Decimal("0"), quota - used),
                    pending_days=Decimal("0"),
                )
            )
    if new_rows:
        db.add_all(new_rows)
        db.flush()


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "Y" if value else "N"
    return str(value)


def export_seeded_data(db: Session, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    export_models = [*LOAD_ORDER, ("payroll_items", PayrollItem)]
    for name, model in export_models:
        columns = [column.name for column in model.__table__.columns]
        order = [column.name for column in model.__table__.primary_key.columns]
        statement = select(model).order_by(*(getattr(model, key) for key in order))
        with (export_dir / f"{name}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for row in db.scalars(statement).yield_per(5000):
                writer.writerow(
                    {column: _format_value(getattr(row, column)) for column in columns}
                )


def main() -> None:
    args = parse_args()
    if args.attendance_chunk_size < 500 or args.attendance_chunk_size > 50000:
        raise SystemExit("--attendance-chunk-size must be between 500 and 50000")
    args.data_dir = args.data_dir.resolve()
    start = time.perf_counter()
    Base.metadata.create_all(bind=engine)
    counts: dict[str, int] = {}
    with SessionLocal() as db:
        with db.begin():
            for name, model in LOAD_ORDER:
                size = args.attendance_chunk_size if name == "attendance" else CHUNK_SIZE
                loaded = 0
                for records in _source_batches(
                    name, model, args.data_dir, size, args.attendance_limit
                ):
                    _upsert(db, model, records)
                    loaded += len(records)
                counts[name] = loaded
            # payroll_items.csv in the kit is a validation answer key. It is never
            # loaded into the application's PayrollItem table; that table contains
            # rows calculated from salary, attendance, rates, tax, and review inputs.
            calculated = [
                _record(PayrollItem, row, number)
                for number, row in enumerate(calculate_payroll(args.data_dir), start=1)
            ]
            db.execute(delete(PayrollItem))
            _upsert(db, PayrollItem, calculated)
            counts["payroll_items"] = len(calculated)
            _seed_missing_leave_balances(db)
        export_seeded_data(db, args.export_dir)

    elapsed = time.perf_counter() - start
    for name, count in counts.items():
        print(f"{name}: {count:,} rows loaded")
    print(f"Database exports written to {args.export_dir.resolve()}")
    print(f"Seed complete in {elapsed:.1f} seconds; re-running updates rows idempotently.")


if __name__ == "__main__":
    main()
