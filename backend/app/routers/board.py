from fastapi import APIRouter, Depends

from backend.app.auth import get_current_user
from backend.app.dependencies import board_repository
from backend.app.models import BoardStateModel

router = APIRouter(prefix="/api", tags=["board"])


@router.get("/board", response_model=BoardStateModel)
def get_board(username: str = Depends(get_current_user)) -> dict:
    return board_repository.get_active_board(username)


@router.put("/board", response_model=BoardStateModel)
def update_board(
    payload: BoardStateModel,
    username: str = Depends(get_current_user),
) -> dict:
    return board_repository.update_active_board(username, payload.model_dump())
