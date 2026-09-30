import pytest

def test_register_and_login(client, clear_rate_limits):
    # Register
    resp = client.post("/api/auth/register", json={"username": "user_a", "password": "supersecretpassword"})
    assert resp.status_code == 201
    
    # Login
    resp = client.post("/api/auth/login", json={"username": "user_a", "password": "supersecretpassword"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "user_a"

def test_wrong_password(client, clear_rate_limits):
    client.post("/api/auth/register", json={"username": "user_a", "password": "supersecretpassword"})
    resp = client.post("/api/auth/login", json={"username": "user_a", "password": "wrongpassword123"})
    assert resp.status_code == 401

def test_unknown_username(client, clear_rate_limits):
    resp = client.post("/api/auth/login", json={"username": "unknown_user", "password": "somepassword123"})
    assert resp.status_code == 401
    
def test_logout(client, clear_rate_limits):
    client.post("/api/auth/register", json={"username": "user_a", "password": "supersecretpassword"})
    resp = client.post("/api/auth/login", json={"username": "user_a", "password": "supersecretpassword"})
    token = resp.json()["access_token"]
    
    # Logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 204
    
    # Reuse token should fail
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401
