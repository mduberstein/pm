from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def auth_header() -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_board_requires_authentication(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    response = client.get("/api/board")

    assert response.status_code == 401


def test_get_board_returns_default_for_new_user(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    response = client.get("/api/board", headers=auth_header())

    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 5
    assert "card-1" in data["cards"]


def test_put_board_persists_changes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    headers = auth_header()
    updated_payload = {
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
                "title": "Updated from integration test",
                "details": "Updated details",
            }
        },
    }

    update_response = client.put("/api/board", headers=headers, json=updated_payload)
    assert update_response.status_code == 200

    read_response = client.get("/api/board", headers=headers)
    assert read_response.status_code == 200
    assert read_response.json() == updated_payload


def test_put_board_rejects_invalid_shape(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "integration.db"))

    headers = auth_header()
    invalid_payload = {
        "columns": [
            {
                "id": "col-backlog",
                "title": "Backlog",
                "cardIds": ["card-404"],
            }
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Mismatch",
                "details": "This should fail",
            }
        },
    }

    response = client.put("/api/board", headers=headers, json=invalid_payload)

    assert response.status_code == 422
