from pydantic import BaseModel, ConfigDict


class DepartmentRead(BaseModel):
    department_id: str
    department_name: str
    cost_center: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleRead(BaseModel):
    role_id: str
    department_id: str
    role_title: str
    level: int
    grade: str
    overtime_eligible: bool
    band_year: int

    model_config = ConfigDict(from_attributes=True)
