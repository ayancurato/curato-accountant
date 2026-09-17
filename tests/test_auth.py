def test_login(client):
    response = client.post("/api/v1/auth/login", data={"username": "test@test.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_unauthorized_access(client):
    response = client.get("/api/v1/company")
    assert response.status_code == 401

def test_authenticated_access(client, auth_headers):
    response = client.get("/api/v1/company", headers=auth_headers)
    assert response.status_code == 200
