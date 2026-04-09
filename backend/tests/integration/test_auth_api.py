from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_login_returns_token_for_valid_credentials() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 10


def test_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "bad-password"},
    )
    assert response.status_code == 401


def test_me_requires_valid_token() -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json() == {"username": "user"}
