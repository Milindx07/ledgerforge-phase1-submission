from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.exceptions import http_exception_handler, validation_exception_handler

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="LedgerForge Phase 1 API for employees, departments, teams, and seed data.",
)

app.include_router(api_router)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
