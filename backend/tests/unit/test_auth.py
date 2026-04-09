from fastapi import HTTPException

from backend.app.auth import (
    create_access_token,
    decode_access_token,
    validate_credentials,
)


def test_validate_credentials_accepts_mvp_credentials() -> None:
    assert validate_credentials("user", "password") is True


def test_validate_credentials_rejects_invalid_credentials() -> None:
    assert validate_credentials("user", "wrong") is False


def test_token_roundtrip_returns_username() -> None:
    token = create_access_token("user")
    assert decode_access_token(token) == "user"


def test_expired_token_is_rejected() -> None:
    expired = create_access_token("user", expires_minutes=-1)
    try:
        decode_access_token(expired)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected expired token to fail.")
