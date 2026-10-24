from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department


def list_departments(db: Session) -> list[Department]:
    return db.scalars(select(Department).order_by(Department.department_id)).all()


def get_department(db: Session, department_id: str) -> Department | None:
    return db.get(Department, department_id)
