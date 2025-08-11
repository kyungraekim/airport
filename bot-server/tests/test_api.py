import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Model Validation Bot API"

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_execute_command():
    """Test command execution endpoint."""
    command_data = {
        "command": "/help",
        "user_id": "test-user"
    }
    response = client.post("/commands/execute", json=command_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["command"] == "/help"

def test_execute_invalid_command():
    """Test execution of invalid command."""
    command_data = {
        "command": "/invalid",
        "user_id": "test-user"
    }
    response = client.post("/commands/execute", json=command_data)
    assert response.status_code == 400

def test_get_active_jobs():
    """Test getting active jobs."""
    response = client.get("/jobs/active")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_nonexistent_job_status():
    """Test getting status of nonexistent job."""
    response = client.get("/jobs/nonexistent-job-id/status")
    assert response.status_code == 404