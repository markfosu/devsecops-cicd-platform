import pytest

from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"
    assert data["service"] == "devsecops-cicd-platform"


def test_status_endpoint(client):
    response = client.get("/api/v1/status")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "operational"
    assert data["version"] == "1.0.0"


def test_info_endpoint(client):
    response = client.get("/api/v1/info")

    assert response.status_code == 200

    data = response.get_json()

    assert data["application"] == "DevSecOps CI/CD Platform"
    assert data["environment"] == "development"