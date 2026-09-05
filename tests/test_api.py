import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_policies_endpoint():
    response = client.get("/policies")
    assert response.status_code == 200
    data = response.json()
    assert "MAX_RETRIES" in data
    assert "MAX_AUTOMATED_AMOUNT" in data

def test_list_payments_endpoint():
    response = client.get("/payments?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert "total" in data

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "How much revenue is currently at risk?"})
    assert response.status_code == 200
    assert "reply" in response.json()
