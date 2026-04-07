import subprocess
import time
from pathlib import Path

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
    finally:
        process.terminate()
        process.wait(timeout=5)
