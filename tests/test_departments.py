def test_list_departments(client):
    response = client.get("/departments")

    assert response.status_code == 200
    assert {row["department_id"] for row in response.json()} == {"D01", "D02"}


def test_department_employee_endpoint(client):
    response = client.get("/departments/D01/employees", params={"q": "Anita"})

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["employee_id"] == "EMP-1000"


def test_missing_department_returns_consistent_error(client):
    response = client.get("/departments/D99/employees")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "department not found"
