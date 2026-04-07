from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_api_hello_returns_expected_payload() -> None:
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI API"}


def test_root_returns_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
