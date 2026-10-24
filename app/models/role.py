from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"),
        nullable=False,
    )
    role_title: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(80), nullable=False)
    band_min_annual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    band_mid_annual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    band_max_annual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    overtime_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    band_year: Mapped[int] = mapped_column(Integer, nullable=False)

    department = relationship("Department", back_populates="roles")
    employees = relationship("Employee", back_populates="role")
