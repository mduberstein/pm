import subprocess
import time
from pathlib import Path
import os

import httpx

ROOT_DIR = Path(__file__).resolve().parents[3]


def wait_for_server(url: str, timeout_seconds: float = 10.0) -> None:
    started_at = time.time()
    while time.time() - started_at < timeout_seconds:
        try:
            response = httpx.get(url, timeout=1.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise AssertionError("Server did not become ready in time.")


def test_server_serves_html_and_api() -> None:
    db_path = ROOT_DIR / "backend" / "data" / "e2e-test.db"
    if db_path.exists():
        db_path.unlink()

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    process = subprocess.Popen(
        [
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8011",
        ],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    try:
        wait_for_server("http://127.0.0.1:8011/")

        root_response = httpx.get("http://127.0.0.1:8011/", timeout=3.0)
        assert root_response.status_code == 200
        assert (
            "Kanban Studio" in root_response.text
            or "Hello from PM MVP" in root_response.text
        )

        api_response = httpx.get("http://127.0.0.1:8011/api/hello", timeout=3.0)
        assert api_response.status_code == 200
        assert api_response.json() == {"message": "Hello from FastAPI API"}

        login_response = httpx.post(
            "http://127.0.0.1:8011/api/auth/login",
            json={"username": "user", "password": "password"},
            timeout=3.0,
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        board_response = httpx.get(
            "http://127.0.0.1:8011/api/board",
            headers=headers,
            timeout=3.0,
        )
        assert board_response.status_code == 200

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
                    "title": "Persisted from e2e",
                    "details": "Persisted details",
                }
            },
        }

        update_response = httpx.put(
            "http://127.0.0.1:8011/api/board",
            headers=headers,
            json=updated_board,
            timeout=3.0,
        )
        assert update_response.status_code == 200

        reloaded_response = httpx.get(
            "http://127.0.0.1:8011/api/board",
            headers=headers,
            timeout=3.0,
        )
        assert reloaded_response.status_code == 200
        assert reloaded_response.json() == updated_board
        assert db_path.exists()
    finally:
        process.terminate()
        process.wait(timeout=5)
        if db_path.exists():
            db_path.unlink()
