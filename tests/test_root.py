def test_root_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "mywebapp" in response.text
    assert "/items" in response.text
