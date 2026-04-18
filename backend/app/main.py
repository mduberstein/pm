from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, model_validator

from backend.app import ai_client
from backend.app.auth import create_access_token, get_current_user, validate_credentials
from backend.app.board_repository import BoardRepository
from backend.app.db import ensure_database

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = STATIC_DIR / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database()
    yield


app = FastAPI(title="PM MVP Backend", lifespan=lifespan)
board_repository = BoardRepository()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CardModel(BaseModel):
    id: str
    title: str
    details: str


class ColumnModel(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardStateModel(BaseModel):
    columns: list[ColumnModel]
    cards: dict[str, CardModel]

    @model_validator(mode="after")
    def validate_board_references(self) -> "BoardStateModel":
        card_keys = set(self.cards.keys())

        for key, card in self.cards.items():
            if card.id != key:
                raise ValueError(f"Card key/id mismatch for '{key}'.")

        referenced_card_ids = [
            card_id for column in self.columns for card_id in column.cardIds
        ]
        unknown_ids = [card_id for card_id in referenced_card_ids if card_id not in card_keys]
        if unknown_ids:
            raise ValueError("Column references unknown card IDs.")

        return self


class ChatRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Prompt cannot be empty.")
        return trimmed


class ChatResponse(BaseModel):
    assistant: str


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI API"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not validate_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(payload.username)
    return LoginResponse(access_token=token)


@app.get("/api/auth/me")
def current_user(username: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": username}


@app.get("/api/board", response_model=BoardStateModel)
def get_board(username: str = Depends(get_current_user)) -> dict:
    return board_repository.get_active_board(username)


@app.put("/api/board", response_model=BoardStateModel)
def update_board(
    payload: BoardStateModel,
    username: str = Depends(get_current_user),
) -> dict:
    return board_repository.update_active_board(username, payload.model_dump())


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    username: str = Depends(get_current_user),
) -> ChatResponse:
    _ = username
    try:
        assistant_reply = ai_client.fetch_assistant_reply(payload.prompt)
    except ai_client.OpenRouterError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return ChatResponse(assistant=assistant_reply)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
