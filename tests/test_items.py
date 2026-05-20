from datetime import datetime


def test_list_items_empty(client, mock_db):
    mock_db["cursor"].fetchall.return_value = []
    response = client.get("/items", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_items_with_data_json(client, mock_db):
    mock_db["cursor"].fetchall.return_value = [
        {"id": 1, "name": "Laptop"},
        {"id": 2, "name": "Mouse"},
    ]
    response = client.get("/items", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Laptop"


def test_list_items_html(client, mock_db):
    mock_db["cursor"].fetchall.return_value = [{"id": 1, "name": "Laptop"}]
    response = client.get("/items", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "Laptop" in response.text
    assert "<table" in response.text


def test_create_item(client, mock_db):
    mock_db["cursor"].lastrowid = 42
    response = client.post("/items", json={"name": "Keyboard", "quantity": 10})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 42
    assert data["name"] == "Keyboard"
    assert data["quantity"] == 10


def test_get_item_found(client, mock_db):
    mock_db["cursor"].fetchone.return_value = {
        "id": 1,
        "name": "Laptop",
        "quantity": 5,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }
    response = client.get("/items/1", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Laptop"


def test_get_item_html(client, mock_db):
    mock_db["cursor"].fetchone.return_value = {
        "id": 1,
        "name": "Laptop",
        "quantity": 5,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }
    response = client.get("/items/1", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "Laptop" in response.text


def test_get_item_not_found(client, mock_db):
    mock_db["cursor"].fetchone.return_value = None
    response = client.get("/items/999")
    assert response.status_code == 404


def test_create_item_validation_error(client, mock_db):
    response = client.post("/items", json={"name": "X", "quantity": "not a number"})
    assert response.status_code == 422
