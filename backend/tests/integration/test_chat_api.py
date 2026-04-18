from fastapi.testclient import TestClient

from backend.app import ai_client
from backend.app.main import app

client = TestClient(app)


def auth_header() -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_requires_authentication() -> None:
    response = client.post("/api/chat", json={"prompt": "2+2"})

    assert response.status_code == 401


def test_chat_returns_assistant_text(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    captured: dict[str, str] = {}

    def fake_fetch(prompt: str, timeout_seconds: float = 20.0) -> str:
        _ = timeout_seconds
        captured["prompt"] = prompt
        return "2+2 is 4"

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={"prompt": "Please solve 2+2"},
    )

    assert response.status_code == 200
    assert response.json() == {"assistant": "2+2 is 4"}
    assert captured["prompt"] == "Please solve 2+2"


def test_chat_surfaces_provider_error_envelope(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    def fake_fetch(prompt: str, timeout_seconds: float = 20.0) -> str:
        _ = prompt
        _ = timeout_seconds
        raise ai_client.OpenRouterError("OpenRouter request failed.", status_code=502)

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={"prompt": "Please solve 2+2"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter request failed."}


def test_chat_rejects_empty_prompt(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={"prompt": "   "},
    )

    assert response.status_code == 422
