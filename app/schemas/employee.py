from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class EmployeeBase(BaseModel):
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    work_email: EmailStr | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    hire_date: date | None = None
    exit_date: date | None = None
    employment_status: str | None = "Active"
    employment_type: str | None = "Permanent"
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    work_location: str | None = None
    work_mode: str | None = None
    highest_education: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def names_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("name cannot be empty")
        return value.strip() if isinstance(value, str) else value

    @field_validator("hire_date")
    @classmethod
    def hire_date_cannot_be_future(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("joining date cannot be in the future")
        return value


class EmployeeCreate(EmployeeBase):
    employee_id: str = Field(max_length=20)
    first_name: str = Field(max_length=80)
    last_name: str = Field(max_length=80)
    work_email: EmailStr
    hire_date: date


class EmployeeUpdate(EmployeeBase):
    employment_status: str | None = None
    employment_type: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "EmployeeUpdate":
        if not self.model_dump(exclude_none=True):
            raise ValueError("at least one field must be provided")
        return self


class EmployeeRead(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    full_name: str
    work_email: EmailStr
    gender: str | None = None
    date_of_birth: date | None = None
    hire_date: date
    exit_date: date | None = None
    employment_status: str
    employment_type: str | None = None
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    phone_number: str | None = None
    work_location: str | None = None
    work_mode: str | None = None
    highest_education: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
