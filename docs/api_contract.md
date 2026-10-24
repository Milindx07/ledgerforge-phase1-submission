# LedgerForge Phase 1 API Contract

Base URL: `http://localhost:8000`

## Health

| Method | Path | Purpose | Success |
| --- | --- | --- | --- |
| GET | `/health` | Container and service health check | `200 {"status": "ok"}` |

## Employees

| Method | Path | Purpose | Request | Success |
| --- | --- | --- | --- | --- |
| POST | `/employees` | Create an employee | `EmployeeCreate` JSON | `201 EmployeeRead` |
| GET | `/employees` | List active employees with pagination, department filter, and search | Query: `page`, `size`, `department`, `q` | `200 Page[EmployeeRead]` |
| GET | `/employees/{employee_id}` | Read one employee | Path: `employee_id` | `200 EmployeeRead` |
| PATCH | `/employees/{employee_id}` | Partially update an employee | `EmployeeUpdate` JSON | `200 EmployeeRead` |
| DELETE | `/employees/{employee_id}` | Soft delete an employee by setting `is_active=false` | Path: `employee_id` | `204` |
| GET | `/employees/{employee_id}/team` | List direct reports for a manager | Path: `employee_id` | `200 EmployeeRead[]` |

## Departments

| Method | Path | Purpose | Request | Success |
| --- | --- | --- | --- | --- |
| GET | `/departments` | List departments | None | `200 DepartmentRead[]` |
| GET | `/departments/{department_id}/employees` | List active employees in one department | Query: `page`, `size`, `q` | `200 Page[EmployeeRead]` |

## Error Format

All API errors use one shape.

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request payload or query parameters are invalid.",
    "details": []
  }
}
```

## Core Schemas

### EmployeeCreate

Required: `employee_id`, `first_name`, `last_name`, `work_email`, `hire_date`.

Optional: `gender`, `date_of_birth`, `exit_date`, `employment_status`, `employment_type`, `department_id`, `role_id`, `manager_id`, `phone_number`, `work_location`, `work_mode`, `highest_education`.

Validation:

- `work_email` must be a valid email address and unique.
- `first_name` and `last_name` cannot be blank.
- `hire_date` cannot be in the future.

### Page

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "size": 20
}
```
