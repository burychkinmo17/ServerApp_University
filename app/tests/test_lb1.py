from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_server_info():
    """Проверяем маршрут /info/server (TC06)"""
    response = client.get("/info/server")
    assert response.status_code == 200
    data = response.json()
    assert "python_version" in data
    assert "server_interface" in data

def test_client_info():
    """Проверяем маршрут /info/client (TC07)"""
    headers = {"user-agent": "FastAPI-Test-Agent"}
    response = client.get("/info/client", headers=headers)
    assert response.status_code == 200
    assert response.json()["user_agent"] == "FastAPI-Test-Agent"

def test_nonexistent_route():
    """Проверка на 404 (TC12)"""
    response = client.get("/info/nonexistent")
    assert response.status_code == 404