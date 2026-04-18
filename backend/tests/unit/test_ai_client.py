import pytest

from backend.app.ai_client import (
    OPENROUTER_MODEL,
    OPENROUTER_SYSTEM_PROMPT,
    OpenRouterError,
    build_openrouter_request,
    parse_openrouter_response,
)


def test_build_openrouter_request_uses_locked_model_and_context() -> None:
    request_payload = build_openrouter_request(
        "2+2",
        board_state={"columns": [], "cards": {}},
        history=[
            {"role": "user", "content": "Earlier request"},
            {"role": "assistant", "content": "Earlier response"},
        ],
    )

    assert request_payload == {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": OPENROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": "Earlier request"},
            {"role": "assistant", "content": "Earlier response"},
            {
                "role": "user",
                "content": '{"prompt": "2+2", "board": {"columns": [], "cards": {}}}',
            },
        ],
    }


def test_parse_openrouter_response_returns_text_content() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": "4",
                }
            }
        ]
    }

    assert parse_openrouter_response(payload) == "4"


def test_parse_openrouter_response_handles_content_parts() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "Part one."},
                        {"type": "text", "text": "Part two."},
                    ]
                }
            }
        ]
    }

    assert parse_openrouter_response(payload) == "Part one.\nPart two."


def test_parse_openrouter_response_rejects_invalid_payload() -> None:
    with pytest.raises(OpenRouterError) as exc:
        parse_openrouter_response({"choices": []})

    assert "invalid response" in exc.value.message.lower()
