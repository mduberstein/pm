import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from backend.app import ai_client
from backend.app.auth import get_current_user
from backend.app.dependencies import board_repository
from backend.app.models import BoardStateModel, ChatAIResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    username: str = Depends(get_current_user),
) -> ChatResponse:
    db_board, snapshot_json = board_repository.get_active_board_with_snapshot(username)
    board_for_ai = payload.board.model_dump() if payload.board is not None else db_board
    history_payload = [message.model_dump() for message in payload.history]

    try:
        assistant_reply = ai_client.fetch_assistant_reply(
            payload.prompt,
            board_state=board_for_ai,
            history=history_payload,
        )
    except ai_client.OpenRouterError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    try:
        parsed_ai_payload = json.loads(assistant_reply)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned invalid JSON.",
        ) from exc

    if not isinstance(parsed_ai_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned unexpected response format.",
        )

    try:
        structured_response = ChatAIResponse.model_validate(parsed_ai_payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response did not match expected schema.",
        ) from exc

    saved_board: BoardStateModel | None = None
    assistant_message = structured_response.assistant
    if structured_response.board is not None:
        persisted = board_repository.update_active_board_if_unchanged(
            username,
            structured_response.board.model_dump(),
            snapshot_json,
        )
        if persisted is not None:
            saved_board = BoardStateModel.model_validate(persisted)
        else:
            assistant_message = (
                "⚠️ Board update suspended — a concurrent manual change was made "
                "while the AI was processing, so no AI modifications were applied. "
                "Re-send your request if you still want this change.\n\n"
                + structured_response.assistant
            )

    return ChatResponse(assistant=assistant_message, board=saved_board)
