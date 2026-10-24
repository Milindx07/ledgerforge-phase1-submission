from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Page
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services import employees as employee_service
from app.services.employees import EmployeeConflictError

router = APIRouter(prefix="/employees")


@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    department: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> Page[EmployeeRead]:
    items, total = employee_service.list_employees(
        db,
        page=page,
        size=size,
        department=department,
        q=q,
    )
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> EmployeeRead:
    try:
        return employee_service.create_employee(db, payload)
    except EmployeeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: str, db: Session = Depends(get_db)) -> EmployeeRead:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
) -> EmployeeRead:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    try:
        return employee_service.update_employee(db, employee, payload)
    except EmployeeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, db: Session = Depends(get_db)) -> None:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    employee_service.soft_delete_employee(db, employee)


@router.get("/{employee_id}/team", response_model=list[EmployeeRead])
def get_team(employee_id: str, db: Session = Depends(get_db)) -> list[EmployeeRead]:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    return employee_service.list_direct_reports(db, employee_id)
