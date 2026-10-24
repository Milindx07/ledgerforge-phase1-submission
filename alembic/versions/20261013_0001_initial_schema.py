"""initial schema

Revision ID: 20261013_0001
Revises:
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261013_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("department_id", sa.String(length=10), nullable=False),
        sa.Column("department_name", sa.String(length=120), nullable=False),
        sa.Column("cost_center", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("department_id"),
        sa.UniqueConstraint("cost_center"),
        sa.UniqueConstraint("department_name"),
    )

    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=10), nullable=False),
        sa.Column("department_id", sa.String(length=10), nullable=False),
        sa.Column("role_title", sa.String(length=160), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=80), nullable=False),
        sa.Column("band_min_annual", sa.Numeric(14, 2), nullable=False),
        sa.Column("band_mid_annual", sa.Numeric(14, 2), nullable=False),
        sa.Column("band_max_annual", sa.Numeric(14, 2), nullable=False),
        sa.Column("overtime_eligible", sa.Boolean(), nullable=False),
        sa.Column("band_year", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"]),
        sa.PrimaryKeyConstraint("role_id"),
    )

    op.create_table(
        "employees",
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("work_email", sa.String(length=255), nullable=False),
        sa.Column("gender", sa.String(length=40), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("employment_status", sa.String(length=40), nullable=False),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("department_id", sa.String(length=10), nullable=True),
        sa.Column("role_id", sa.String(length=10), nullable=True),
        sa.Column("manager_id", sa.String(length=20), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("work_location", sa.String(length=80), nullable=True),
        sa.Column("work_mode", sa.String(length=40), nullable=True),
        sa.Column("highest_education", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.PrimaryKeyConstraint("employee_id"),
        sa.UniqueConstraint("work_email"),
    )
    op.create_index("ix_employees_department_active", "employees", ["department_id", "is_active"])
    op.create_index("ix_employees_full_name", "employees", ["full_name"])
    op.create_index("ix_employees_manager_id", "employees", ["manager_id"])
    op.create_index("ix_employees_name", "employees", ["first_name", "last_name"])
    op.create_index("ix_employees_work_email", "employees", ["work_email"])

    op.create_table(
        "employee_assignments",
        sa.Column("assignment_id", sa.String(length=20), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("department_id", sa.String(length=10), nullable=False),
        sa.Column("role_id", sa.String(length=10), nullable=False),
        sa.Column("job_level", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.String(length=20), nullable=True),
        sa.Column("change_reason", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.PrimaryKeyConstraint("assignment_id"),
    )
    op.create_index("ix_employee_assignments_employee_id", "employee_assignments", ["employee_id"])

    op.create_table(
        "salary_structures",
        sa.Column("structure_id", sa.String(length=20), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("component_id", sa.String(length=30), nullable=False),
        sa.Column("component_name", sa.String(length=120), nullable=False),
        sa.Column("component_type", sa.String(length=40), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("revision_id", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"]),
        sa.PrimaryKeyConstraint("structure_id"),
    )
    op.create_index("ix_salary_structures_employee_id", "salary_structures", ["employee_id"])

    op.create_table(
        "attendance",
        sa.Column("attendance_id", sa.String(length=20), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("weekday", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("leave_type_code", sa.String(length=20), nullable=True),
        sa.Column("check_in", sa.String(length=10), nullable=True),
        sa.Column("check_out", sa.String(length=10), nullable=True),
        sa.Column("hours_worked", sa.Numeric(5, 2), nullable=True),
        sa.Column("overtime_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("late_flag", sa.String(length=5), nullable=True),
        sa.Column("source", sa.String(length=60), nullable=True),
        sa.Column("data_quality_flag", sa.String(length=60), nullable=True),
        sa.Column("department_id", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"]),
        sa.PrimaryKeyConstraint("attendance_id"),
    )
    op.create_index("ix_attendance_attendance_date", "attendance", ["attendance_date"])
    op.create_index("ix_attendance_employee_id", "attendance", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_attendance_employee_id", table_name="attendance")
    op.drop_index("ix_attendance_attendance_date", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_salary_structures_employee_id", table_name="salary_structures")
    op.drop_table("salary_structures")
    op.drop_index("ix_employee_assignments_employee_id", table_name="employee_assignments")
    op.drop_table("employee_assignments")
    op.drop_index("ix_employees_work_email", table_name="employees")
    op.drop_index("ix_employees_name", table_name="employees")
    op.drop_index("ix_employees_manager_id", table_name="employees")
    op.drop_index("ix_employees_full_name", table_name="employees")
    op.drop_index("ix_employees_department_active", table_name="employees")
    op.drop_table("employees")
    op.drop_table("roles")
    op.drop_table("departments")
