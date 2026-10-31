from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attendance, Holiday, LeaveBalance, LeaveRequest

ZERO = Decimal("0")


def month_summary(db: Session, employee_id: str, year: int, month: int) -> dict[str, int | Decimal]:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    rows = db.scalars(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start,
            Attendance.attendance_date <= end,
        )
    ).all()
    counts = {"present": 0, "wfh": 0, "absent": ZERO, "late": 0, "overtime_hours": ZERO}
    for row in rows:
        status = row.status.upper()
        if status == "PRESENT":
            counts["present"] += 1
        elif status == "WFH":
            counts["wfh"] += 1
        elif status in {"ABSENT_LOP", "UNPAID_LEAVE"}:
            counts["absent"] += Decimal("1")
        elif status == "HALF_DAY_UNPAID":
            counts["absent"] += Decimal("0.5")
        if (row.late_flag or "").upper() in {"Y", "YES", "TRUE"}:
            counts["late"] += 1
        # MISSING_CHECKOUT is treated as attendance for the recorded status, but its
        # work/overtime duration is unverified and therefore contributes zero hours.
        if row.data_quality_flag != "MISSING_CHECKOUT" and row.overtime_hours is not None:
            counts["overtime_hours"] += Decimal(row.overtime_hours)
    return counts


def count_leave_days(db: Session, start_date: date, end_date: date) -> Decimal:
    if end_date < start_date:
        raise ValueError("end date must be on or after start date")
    holidays = set(
        db.scalars(select(Holiday.holiday_date).where(Holiday.holiday_date.between(start_date, end_date))).all()
    )
    days = sum(
        1 for day in (start_date.fromordinal(n) for n in range(start_date.toordinal(), end_date.toordinal() + 1))
        if day.weekday() < 5 and day not in holidays
    )
    return Decimal(days)


def submit_leave(
    db: Session,
    *,
    request_id: str,
    employee_id: str,
    leave_type_code: str,
    start_date: date,
    end_date: date,
    reason: str,
    financial_year: str,
    applied_on: date | None = None,
) -> LeaveRequest:
    days = count_leave_days(db, start_date, end_date)
    if days <= ZERO:
        raise ValueError("leave period contains no working days")
    balance = db.get(LeaveBalance, (employee_id, leave_type_code, financial_year))
    if balance is None or Decimal(balance.balance_days) - Decimal(balance.pending_days) < days:
        raise ValueError("insufficient leave balance")
    balance.pending_days = Decimal(balance.pending_days) + days
    request = LeaveRequest(
        leave_request_id=request_id,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        start_date=start_date,
        end_date=end_date,
        days=days,
        reason=reason,
        status="PENDING",
        applied_on=applied_on or date.today(),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def decide_leave(
    db: Session,
    request: LeaveRequest,
    *,
    approve: bool,
    financial_year: str,
    approver_id: str,
    note: str | None = None,
    decided_on: date | None = None,
) -> LeaveRequest:
    if request.status != "PENDING":
        raise ValueError("only pending leave requests can be decided")
    balance = db.get(LeaveBalance, (request.employee_id, request.leave_type_code, financial_year))
    if balance is None:
        raise ValueError("leave balance not found")
    days = Decimal(request.days)
    balance.pending_days = max(ZERO, Decimal(balance.pending_days) - days)
    if approve:
        if Decimal(balance.balance_days) < days:
            raise ValueError("insufficient leave balance")
        balance.used_days = Decimal(balance.used_days) + days
        balance.balance_days = Decimal(balance.balance_days) - days
        request.status = "APPROVED"
    else:
        request.status = "REJECTED"
    request.approver_id = approver_id
    request.decided_on = decided_on or date.today()
    request.decision_note = note
    db.commit()
    db.refresh(request)
    return request
