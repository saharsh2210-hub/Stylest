from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core.auth import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    auth_enabled,
    clear_login_failures,
    create_session_token,
    login_rate_limited,
    record_login_failure,
    session_cookie_secure,
    verify_app_password,
    verify_session_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


@router.get("/session")
def session_status(request: Request):
    enabled = auth_enabled()
    authenticated = not enabled or verify_session_token(request.cookies.get(SESSION_COOKIE))
    return {"authenticated": authenticated, "password_required": enabled}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    if not auth_enabled():
        return {"authenticated": True}
    if login_rate_limited(request):
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again in 15 minutes.")
    if not verify_app_password(payload.password):
        record_login_failure(request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="That password didn’t match.")
    clear_login_failures(request)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="lax",
        path="/",
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="lax",
        path="/",
    )
    return {"authenticated": False}
