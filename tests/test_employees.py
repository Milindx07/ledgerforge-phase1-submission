from datetime import date, timedelta


def employee_payload(**overrides):
    payload = {
        "employee_id": "EMP-2000",
        "first_name": "Meera",
        "last_name": "Iyer",
        "work_email": "meera.iyer@example.com",
        "hire_date": "2024-04-01",
        "department_id": "D01",
        "role_id": "R001",
        "manager_id": "EMP-1000",
        "phone_number": "+91-90000-02000",
        "employment_type": "Permanent",
    }
    payload.update(overrides)
    return payload


def test_create_read_update_and_soft_delete_employee(client):
    created = client.post("/employees", json=employee_payload())

    assert created.status_code == 201
    assert created.json()["full_name"] == "Meera Iyer"

    fetched = client.get("/employees/EMP-2000")
    assert fetched.status_code == 200
    assert fetched.json()["work_email"] == "meera.iyer@example.com"

    updated = client.patch("/employees/EMP-2000", json={"last_name": "Menon"})
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Meera Menon"

    deleted = client.delete("/employees/EMP-2000")
    assert deleted.status_code == 204

    listing = client.get("/employees", params={"q": "Meera"})
    assert listing.status_code == 200
    assert listing.json()["total"] == 0


def test_employee_list_supports_pagination_filter_and_search(client):
    response = client.get(
        "/employees",
        params={"page": 1, "size": 1, "department": "D01", "q": "rahul"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["employee_id"] == "EMP-1001"


def test_duplicate_email_fails(client):
    response = client.post(
        "/employees",
        json=employee_payload(work_email="rahul.mehta@example.com"),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "409"


def test_bad_input_uses_consistent_error_shape(client):
    future = (date.today() + timedelta(days=3)).isoformat()
    response = client.post(
        "/employees",
        json=employee_payload(first_name="", hire_date=future),
    )

    assert response.status_code == 422
    assert "error" in response.json()


def test_direct_reports_endpoint(client):
    response = client.get("/employees/EMP-1000/team")

    assert response.status_code == 200
    assert [row["employee_id"] for row in response.json()] == ["EMP-1001"]
