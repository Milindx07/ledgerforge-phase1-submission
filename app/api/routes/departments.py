from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Page
from app.schemas.department import DepartmentRead
from app.schemas.employee import EmployeeRead
from app.services import departments as department_service
from app.services import employees as employee_service

router = APIRouter(prefix="/departments")


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)) -> list[DepartmentRead]:
    return department_service.list_departments(db)


@router.get("/{department_id}/employees", response_model=Page[EmployeeRead])
def list_department_employees(
    department_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
    db: Session = Depends(get_db),
) -> Page[EmployeeRead]:
    if department_service.get_department(db, department_id) is None:
        raise HTTPException(status_code=404, detail="department not found")

    items, total = employee_service.list_employees(
        db,
        page=page,
        size=size,
        department=department_id,
        q=q,
    )
    return Page(items=items, total=total, page=page, size=size)
