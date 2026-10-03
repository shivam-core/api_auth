import pytest
import io
from fastapi.testclient import TestClient

def test_document_lifecycle(client: TestClient):
    # 1. Register and login
    import uuid
    username = f"usr_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json={"username": username, "password": "supersecretpassword"})
    login_resp = client.post("/api/auth/login", json={"username": username, "password": "supersecretpassword"})
    assert "access_token" in login_resp.json(), f"Login failed: {login_resp.json()}"
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload a document
    file_content = b"This is a secret document."
    files = {"file": ("secret.txt", file_content, "text/plain")}
    data = {"display_name": "My Secret", "description": "Highly classified"}
    
    upload_resp = client.post("/api/documents", files=files, data=data, headers=headers)
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]
    assert upload_resp.json()["display_name"] == "My Secret"
    assert upload_resp.json()["byte_length"] == len(file_content)
    
    # 3. List documents
    list_resp = client.get("/api/documents", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 1
    
    # 4. Get metadata
    get_resp = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["filename"] == "secret.txt"
    
    # 5. Get content
    content_resp = client.get(f"/api/documents/{doc_id}/content", headers=headers)
    assert content_resp.status_code == 200
    assert content_resp.content == file_content
    
    # 6. Update metadata
    update_resp = client.patch(f"/api/documents/{doc_id}", json={"display_name": "Updated Secret"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["display_name"] == "Updated Secret"
    assert update_resp.json()["version"] == 2
    
    # 7. Check envelope
    env_resp = client.get(f"/api/documents/{doc_id}/envelope", headers=headers)
    assert env_resp.status_code == 200
    assert "metadata_nonce_b64" in env_resp.json()
    assert env_resp.json()["version"] == 2
    
    # 8. Delete
    del_resp = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 204
    
    list_empty = client.get("/api/documents", headers=headers)
    assert len(list_empty.json()["items"]) == 0
