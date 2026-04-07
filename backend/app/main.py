from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = STATIC_DIR / "frontend"

app = FastAPI(title="PM MVP Backend")


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI API"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
