from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weekday: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    leave_type_code: Mapped[str | None] = mapped_column(String(20))
    check_in: Mapped[str | None] = mapped_column(String(10))
    check_out: Mapped[str | None] = mapped_column(String(10))
    hours_worked: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    overtime_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    late_flag: Mapped[str | None] = mapped_column(String(5))
    source: Mapped[str | None] = mapped_column(String(60))
    data_quality_flag: Mapped[str | None] = mapped_column(String(60))
    department_id: Mapped[str | None] = mapped_column(ForeignKey("departments.department_id"))
