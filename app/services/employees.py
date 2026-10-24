from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeConflictError(ValueError):
    pass


def _full_name(first_name: str, last_name: str) -> str:
    return f"{first_name.strip()} {last_name.strip()}".strip()


def list_employees(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    department: str | None = None,
    q: str | None = None,
) -> tuple[list[Employee], int]:
    query = select(Employee).where(Employee.is_active.is_(True))

    if department:
        query = query.where(Employee.department_id == department)

    if q:
        pattern = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Employee.first_name).like(pattern),
                func.lower(Employee.last_name).like(pattern),
                func.lower(Employee.full_name).like(pattern),
                func.lower(Employee.work_email).like(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Employee.employee_id).offset((page - 1) * size).limit(size)
    ).all()
    return rows, total


def get_employee(db: Session, employee_id: str) -> Employee | None:
    return db.get(Employee, employee_id)


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    data = payload.model_dump()
    employee = Employee(
        **data,
        full_name=_full_name(payload.first_name, payload.last_name),
        is_active=data.get("employment_status", "Active") == "Active",
    )
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmployeeConflictError("employee id or work email already exists") from exc
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee: Employee, payload: EmployeeUpdate) -> Employee:
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(employee, field, value)

    if "first_name" in changes or "last_name" in changes:
        employee.full_name = _full_name(employee.first_name, employee.last_name)

    if employee.employment_status != "Active":
        employee.is_active = False

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmployeeConflictError("work email already exists") from exc
    db.refresh(employee)
    return employee


def soft_delete_employee(db: Session, employee: Employee) -> None:
    employee.is_active = False
    employee.employment_status = "Inactive"
    db.commit()


def list_direct_reports(db: Session, manager_id: str) -> list[Employee]:
    return db.scalars(
        select(Employee)
        .where(Employee.manager_id == manager_id, Employee.is_active.is_(True))
        .order_by(Employee.full_name)
    ).all()
