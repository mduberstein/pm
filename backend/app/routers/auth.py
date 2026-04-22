from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.auth import create_access_token, get_current_user, validate_credentials
from backend.app.dependencies import limiter
from backend.app.models import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("60/minute")
def login(request: Request, payload: LoginRequest) -> LoginResponse:
    if not validate_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token = create_access_token(payload.username)
    return LoginResponse(access_token=token)


@router.get("/me")
def current_user(username: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": username}
