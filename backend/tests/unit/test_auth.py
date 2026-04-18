from datetime import datetime, timezone

from fastapi import HTTPException
import jwt

from backend.app.auth import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
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


def test_default_token_expiration_is_sufficient() -> None:
    token = create_access_token("user")
    payload = jwt.decode(
        token,
        options={"verify_signature": False, "verify_exp": False},
        algorithms=[JWT_ALGORITHM],
    )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    remaining_minutes = (expires_at - datetime.now(timezone.utc)).total_seconds() / 60

    assert remaining_minutes > 420


def test_token_expiration_uses_env_override(monkeypatch) -> None:
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "120")

    token = create_access_token("user")
    payload = jwt.decode(
        token,
        options={"verify_signature": False, "verify_exp": False},
        algorithms=[JWT_ALGORITHM],
    )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    remaining_minutes = (expires_at - datetime.now(timezone.utc)).total_seconds() / 60

    assert remaining_minutes > 110
    assert remaining_minutes <= 120


def test_invalid_env_expiration_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "invalid")

    token = create_access_token("user")
    payload = jwt.decode(
        token,
        options={"verify_signature": False, "verify_exp": False},
        algorithms=[JWT_ALGORITHM],
    )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    remaining_minutes = (expires_at - datetime.now(timezone.utc)).total_seconds() / 60

    assert remaining_minutes > (JWT_EXPIRE_MINUTES - 10)
