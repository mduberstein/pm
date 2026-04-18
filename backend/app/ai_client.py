import json
import os

import httpx
from fastapi import status

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
OPENROUTER_SYSTEM_PROMPT = (
    "You are a project-management assistant. "
    "Return only valid JSON with exactly these keys: "
    "assistant (string), board (object or null). "
    "Do not include markdown code fences or extra keys."
)


class OpenRouterError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_openrouter_request(
    prompt: str,
    board_state: dict | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": OPENROUTER_SYSTEM_PROMPT,
        }
    ]

    for item in history or []:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            stripped = content.strip()
            if stripped:
                messages.append({"role": role, "content": stripped})

    context_payload = {
        "prompt": prompt,
        "board": board_state or {},
    }
    messages.append(
        {
            "role": "user",
            "content": json.dumps(context_payload),
        }
    )

    return {
        "model": OPENROUTER_MODEL,
        "messages": messages,
    }


def parse_openrouter_response(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterError("OpenRouter returned an invalid response.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise OpenRouterError("OpenRouter returned an invalid response.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise OpenRouterError("OpenRouter returned an invalid response.")

    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        if text:
            return text

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    stripped = text.strip()
                    if stripped:
                        text_parts.append(stripped)

        if text_parts:
            return "\n".join(text_parts)

    raise OpenRouterError("OpenRouter returned an invalid response.")


def _openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterError(
            "OpenRouter API key is not configured.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return api_key


def fetch_assistant_reply(
    prompt: str,
    board_state: dict | None = None,
    history: list[dict[str, str]] | None = None,
    timeout_seconds: float = 20.0,
) -> str:
    headers = {
        "Authorization": f"Bearer {_openrouter_api_key()}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers=headers,
            json=build_openrouter_request(prompt, board_state=board_state, history=history),
            timeout=timeout_seconds,
        )
    except httpx.RequestError as exc:
        raise OpenRouterError("Failed to reach OpenRouter.") from exc

    if response.status_code in {401, 403}:
        raise OpenRouterError("OpenRouter authentication failed.")

    if response.status_code >= 400:
        raise OpenRouterError("OpenRouter request failed.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise OpenRouterError("OpenRouter returned invalid JSON.") from exc

    return parse_openrouter_response(payload)
