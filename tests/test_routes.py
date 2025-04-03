from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    assert "stats" in response.json()