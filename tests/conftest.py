from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, Department, Employee, Role


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        seed_reference_data(db)
        yield db


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_reference_data(db: Session) -> None:
    engineering = Department(
        department_id="D01",
        department_name="Engineering",
        cost_center="CC-100",
        description="Product engineering",
    )
    people = Department(
        department_id="D02",
        department_name="People Operations",
        cost_center="CC-200",
        description="HR and people operations",
    )
    engineer = Role(
        role_id="R001",
        department_id="D01",
        role_title="Software Engineer",
        level=2,
        grade="L2 Executive",
        band_min_annual=720000,
        band_mid_annual=900000,
        band_max_annual=1170000,
        overtime_eligible=False,
        band_year=2026,
    )
    manager = Role(
        role_id="R002",
        department_id="D01",
        role_title="Engineering Manager",
        level=4,
        grade="L4 Manager",
        band_min_annual=1800000,
        band_mid_annual=2200000,
        band_max_annual=2800000,
        overtime_eligible=False,
        band_year=2026,
    )
    boss = Employee(
        employee_id="EMP-1000",
        first_name="Anita",
        last_name="Rao",
        full_name="Anita Rao",
        work_email="anita.rao@example.com",
        hire_date=date(2021, 1, 10),
        employment_status="Active",
        employment_type="Permanent",
        department_id="D01",
        role_id="R002",
        phone_number="+91-90000-01000",
        is_active=True,
    )
    report = Employee(
        employee_id="EMP-1001",
        first_name="Rahul",
        last_name="Mehta",
        full_name="Rahul Mehta",
        work_email="rahul.mehta@example.com",
        hire_date=date(2022, 2, 15),
        employment_status="Active",
        employment_type="Permanent",
        department_id="D01",
        role_id="R001",
        manager_id="EMP-1000",
        phone_number="+91-90000-01001",
        is_active=True,
    )
    db.add_all([engineering, people, engineer, manager, boss, report])
    db.commit()
