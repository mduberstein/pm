import json

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

    captured: dict[str, object] = {}

    def fake_fetch(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        _ = board_state
        _ = timeout_seconds
        captured["prompt"] = prompt
        captured["history"] = history
        return json.dumps({"assistant": "2+2 is 4", "board": None})

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={
            "prompt": "Please solve 2+2",
            "history": [
                {"role": "user", "content": "Earlier question"},
                {"role": "assistant", "content": "Earlier answer"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"assistant": "2+2 is 4", "board": None}
    assert captured["prompt"] == "Please solve 2+2"
    assert captured["history"] == [
        {"role": "user", "content": "Earlier question"},
        {"role": "assistant", "content": "Earlier answer"},
    ]


def test_chat_persists_valid_board_update(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    updated_board = {
        "columns": [
            {
                "id": "col-backlog",
                "title": "Backlog",
                "cardIds": ["card-1"],
            }
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Created by AI",
                "details": "Persisted by chat endpoint",
            }
        },
    }

    def fake_fetch(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        _ = prompt
        _ = board_state
        _ = history
        _ = timeout_seconds
        return json.dumps({"assistant": "Applied update.", "board": updated_board})

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    headers = auth_header()
    response = client.post(
        "/api/chat",
        headers=headers,
        json={"prompt": "Create one card in backlog"},
    )

    assert response.status_code == 200
    assert response.json() == {"assistant": "Applied update.", "board": updated_board}

    board_response = client.get("/api/board", headers=headers)
    assert board_response.status_code == 200
    assert board_response.json() == updated_board


def test_chat_rejects_schema_invalid_response_without_board_mutation(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    headers = auth_header()
    initial_board_response = client.get("/api/board", headers=headers)
    assert initial_board_response.status_code == 200
    initial_board = initial_board_response.json()

    def fake_fetch(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        _ = prompt
        _ = board_state
        _ = history
        _ = timeout_seconds
        return "not-json"

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    response = client.post(
        "/api/chat",
        headers=headers,
        json={"prompt": "Move a card"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "AI service returned invalid JSON."}

    reloaded_board_response = client.get("/api/board", headers=headers)
    assert reloaded_board_response.status_code == 200
    assert reloaded_board_response.json() == initial_board


def test_chat_surfaces_provider_error_envelope(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    def fake_fetch(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        _ = prompt
        _ = board_state
        _ = history
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


def test_chat_skips_board_save_on_concurrent_update(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    ai_board = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-ai"]}],
        "cards": {"card-ai": {"id": "card-ai", "title": "AI card", "details": "From AI"}},
    }
    drag_board = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-drag"]}],
        "cards": {"card-drag": {"id": "card-drag", "title": "Drag card", "details": "From drag"}},
    }

    headers = auth_header()

    def fake_fetch_with_concurrent_drag(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        # Simulate a drag-and-drop saving while AI is thinking
        client.put("/api/board", headers=headers, json=drag_board)
        return json.dumps({"assistant": "Done.", "board": ai_board})

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch_with_concurrent_drag)

    response = client.post(
        "/api/chat",
        headers=headers,
        json={"prompt": "Add a card"},
    )

    assert response.status_code == 200
    body = response.json()
    # AI board is not returned because the concurrent drag took precedence
    assert body["board"] is None
    # Assistant message must surface the suspension, not claim the update succeeded
    assert "suspended" in body["assistant"].lower()
    assert "Done." in body["assistant"]

    # Drag changes were preserved
    board_response = client.get("/api/board", headers=headers)
    assert board_response.json() == drag_board


def test_chat_uses_client_board_for_ai_context(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    client_board = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-local"]}],
        "cards": {"card-local": {"id": "card-local", "title": "Local unsaved card", "details": ""}},
    }
    captured: dict[str, object] = {}

    def fake_fetch(
        prompt: str,
        board_state: dict | None = None,
        history: list[dict[str, str]] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        captured["board_state"] = board_state
        return json.dumps({"assistant": "Got it.", "board": None})

    monkeypatch.setattr(ai_client, "fetch_assistant_reply", fake_fetch)

    client.post(
        "/api/chat",
        headers=auth_header(),
        json={"prompt": "Describe the board", "board": client_board},
    )

    assert captured["board_state"] == client_board


def test_chat_rejects_empty_prompt(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={"prompt": "   "},
    )

    assert response.status_code == 422


def test_chat_rejects_invalid_history_role(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    response = client.post(
        "/api/chat",
        headers=auth_header(),
        json={
            "prompt": "Please solve 2+2",
            "history": [{"role": "system", "content": "Not allowed"}],
        },
    )

    assert response.status_code == 422
