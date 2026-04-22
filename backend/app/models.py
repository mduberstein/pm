from pydantic import BaseModel, Field, field_validator, model_validator


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


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        trimmed = value.strip().lower()
        if trimmed not in {"user", "assistant"}:
            raise ValueError("History role must be 'user' or 'assistant'.")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("History content cannot be empty.")
        return trimmed


class ChatRequest(BaseModel):
    prompt: str
    history: list[ChatMessage] = Field(default_factory=list)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Prompt cannot be empty.")
        return trimmed


class ChatAIResponse(BaseModel):
    assistant: str
    board: BoardStateModel | None = None

    @field_validator("assistant")
    @classmethod
    def validate_assistant(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Assistant response cannot be empty.")
        return trimmed


class ChatResponse(BaseModel):
    assistant: str
    board: BoardStateModel | None = None
