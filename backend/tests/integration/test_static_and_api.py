from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_static_page_serves_root_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_api_endpoint_reachable_from_same_app() -> None:
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from FastAPI API"
