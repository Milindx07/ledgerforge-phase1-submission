from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"

    assignment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False,
        index=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    job_level: Mapped[int] = mapped_column(Integer, nullable=False)
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("employees.employee_id"))
    change_reason: Mapped[str] = mapped_column(String(80), nullable=False)
