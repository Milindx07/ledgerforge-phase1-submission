from fastapi import APIRouter

from app.api.routes import departments, employees, health, phase2

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(employees.router, tags=["employees"])
api_router.include_router(departments.router, tags=["departments"])
api_router.include_router(phase2.router, tags=["attendance", "leave", "payroll", "ledger", "invoices"])
