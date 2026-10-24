from fastapi import APIRouter

from app.api.routes import departments, employees, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(employees.router, tags=["employees"])
api_router.include_router(departments.router, tags=["departments"])
