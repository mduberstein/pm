import os

import httpx
from fastapi import status

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"


class OpenRouterError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_openrouter_request(prompt: str) -> dict[str, object]:
    return {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
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


def fetch_assistant_reply(prompt: str, timeout_seconds: float = 20.0) -> str:
    headers = {
        "Authorization": f"Bearer {_openrouter_api_key()}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers=headers,
            json=build_openrouter_request(prompt),
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
