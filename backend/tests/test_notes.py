import pytest

def get_token(client, username):
    client.post("/api/auth/register", json={"username": username, "password": "supersecretpassword"})
    return client.post("/api/auth/login", json={"username": username, "password": "supersecretpassword"}).json()["access_token"]

def test_crud_notes(client, clear_rate_limits):
    token = get_token(client, "user_a")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create
    resp = client.post("/api/notes", json={"title": "Test Note", "body": "Secret contents here"}, headers=headers)
    assert resp.status_code == 201
    note_id = resp.json()["id"]
    
    # Read
    resp = client.get(f"/api/notes/{note_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Note"
    
    # Update
    resp = client.patch(f"/api/notes/{note_id}", json={"title": "Updated", "body": "New contents"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    
    # Delete
    resp = client.delete(f"/api/notes/{note_id}", headers=headers)
    assert resp.status_code == 204
    
def test_cross_user_isolation(client, clear_rate_limits):
    token_a = get_token(client, "user_a")
    token_b = get_token(client, "user_b")
    
    resp = client.post("/api/notes", json={"title": "A note", "body": "A body"}, headers={"Authorization": f"Bearer {token_a}"})
    note_id = resp.json()["id"]
    
    # B tries to read A's note
    resp = client.get(f"/api/notes/{note_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404
