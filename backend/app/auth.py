from datetime import datetime, timedelta, timezone
from typing import Annotated
import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 480
DEFAULT_JWT_SECRET = "pm-dev-jwt-secret"

security = HTTPBearer(auto_error=False)


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)


def _default_jwt_expire_minutes() -> int:
    configured = os.getenv("JWT_EXPIRE_MINUTES", "").strip()
    if not configured:
        return JWT_EXPIRE_MINUTES

    try:
        parsed = int(configured)
    except ValueError:
        return JWT_EXPIRE_MINUTES

    if parsed <= 0:
        return JWT_EXPIRE_MINUTES

    return parsed


def validate_credentials(username: str, password: str) -> bool:
    # MVP only — replace with DB-backed auth + bcrypt before production.
    return username == "user" and password == "password"


def create_access_token(username: str, expires_minutes: int | None = None) -> str:
    lifetime_minutes = expires_minutes
    if lifetime_minutes is None:
        lifetime_minutes = _default_jwt_expire_minutes()

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)
    payload = {
        "sub": username,
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc

    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    return username


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return decode_access_token(credentials.credentials)
