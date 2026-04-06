from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_static_files():
    response = client.get("/")
    assert response.status_code == 200
    assert "Daystat" in response.text
