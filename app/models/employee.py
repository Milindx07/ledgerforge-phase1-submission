from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_name", "first_name", "last_name"),
        Index("ix_employees_department_active", "department_id", "is_active"),
    )

    employee_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    work_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(40))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[date | None] = mapped_column(Date)
    employment_status: Mapped[str] = mapped_column(String(40), nullable=False, default="Active")
    employment_type: Mapped[str | None] = mapped_column(String(50))
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.department_id"),
        index=True,
    )
    role_id: Mapped[str | None] = mapped_column(ForeignKey("roles.role_id"), index=True)
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("employees.employee_id"), index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30))
    prior_experience_years: Mapped[float | None] = mapped_column(Numeric(6, 2))
    career_gap_months: Mapped[int | None] = mapped_column()
    commute_distance_km: Mapped[float | None] = mapped_column(Numeric(7, 2))
    work_location: Mapped[str | None] = mapped_column(String(80))
    work_mode: Mapped[str | None] = mapped_column(String(40))
    highest_education: Mapped[str | None] = mapped_column(String(120))
    pf_applicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    esi_applicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    notice_period_days: Mapped[int | None] = mapped_column()
    resignation_date: Mapped[date | None] = mapped_column(Date)
    exit_type: Mapped[str | None] = mapped_column(String(40))
    exit_reason: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    department = relationship("Department", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    manager = relationship("Employee", remote_side=[employee_id], back_populates="direct_reports")
    direct_reports = relationship("Employee", back_populates="manager")
