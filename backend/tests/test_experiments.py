import pytest
from fastapi.testclient import TestClient

def test_experiments_bruteforce(client: TestClient):
    resp = client.post("/api/experiments/bruteforce")
    assert resp.status_code == 200
    assert resp.json()["experiment"] == "bruteforce"
    assert resp.json()["passed"] is True

def test_experiments_timing(client: TestClient):
    resp = client.post("/api/experiments/timing")
    assert resp.status_code == 200
    assert resp.json()["experiment"] == "timing"
    assert resp.json()["passed"] is True

def test_experiments_fuzz(client: TestClient):
    resp = client.post("/api/experiments/fuzz")
    assert resp.status_code == 200
    assert resp.json()["experiment"] == "fuzz"
    assert resp.json()["passed"] is True
