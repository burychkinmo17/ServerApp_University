from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_server_info():
    response = client.get("/info/server")
    assert response.status_code == 200
    data = response.json()
    assert "python_version" in data
    assert "server_interface" in data # Проверяем именно этот ключ

def test_client_info():
    response = client.get("/info/client")
    assert response.status_code == 200
    assert "ip" in response.json()

def test_database_info():
    response = client.get("/info/database")
    # Если база в .env настроена верно, вернет 200
    assert response.status_code == 200