def test_alive(client):
    response = client.get("/health/alive")
    assert response.status_code == 200
    assert response.text == "OK"


def test_ready_when_db_available(client, mock_db):
    mock_db["is_ready"].return_value = True
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.text == "OK"


def test_ready_when_db_unavailable(client, mock_db):
    mock_db["is_ready"].return_value = False
    response = client.get("/health/ready")
    assert response.status_code == 500
