import hashlib
import hmac
import os
import secrets
import time

from fastapi import Request

SESSION_COOKIE = "fitcheck_session"
SESSION_MAX_AGE = 30 * 24 * 60 * 60
MAX_LOGIN_ATTEMPTS = 8
LOGIN_WINDOW_SECONDS = 15 * 60
_login_attempts: dict[str, list[float]] = {}


def auth_enabled() -> bool:
    return bool(os.getenv("FITCHECK_APP_PASSWORD"))


def validate_production_auth():
    if os.getenv("FITCHECK_ENV", "").lower() != "production":
        return
    password = os.getenv("FITCHECK_APP_PASSWORD", "")
    secret = os.getenv("FITCHECK_SESSION_SECRET", "")
    if len(password) < 16:
        raise RuntimeError("Set FITCHECK_APP_PASSWORD to a private password of at least 16 characters.")
    if len(secret) < 32:
        raise RuntimeError("Set FITCHECK_SESSION_SECRET to a cryptographically random value of at least 32 characters.")
    if os.getenv("FITCHECK_IMAGE_STORAGE", "local").strip().lower() != "database":
        raise RuntimeError("Use FITCHECK_IMAGE_STORAGE=database for private, persistent production image storage.")


def _sign(timestamp: str) -> str:
    secret = os.getenv("FITCHECK_SESSION_SECRET")
    if not secret:
        if os.getenv("FITCHECK_ENV", "").lower() == "production":
            raise RuntimeError("FITCHECK_SESSION_SECRET is required in production.")
        secret = os.getenv("FITCHECK_APP_PASSWORD", "FITCHECK-local-development-session")
    return hmac.new(secret.encode(), timestamp.encode(), hashlib.sha256).hexdigest()


def create_session_token() -> str:
    timestamp = str(int(time.time()))
    return f"{timestamp}.{_sign(timestamp)}"


def verify_session_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    timestamp, signature = token.split(".", 1)
    if not timestamp.isdecimal() or len(timestamp) > 12:
        return False
    issued_at = int(timestamp)
    now = int(time.time())
    if issued_at > now or now - issued_at > SESSION_MAX_AGE:
        return False
    return secrets.compare_digest(_sign(timestamp), signature)


def login_rate_limited(request: Request) -> bool:
    now = time.monotonic()
    address = request.client.host if request.client else "unknown"
    attempts = [attempt for attempt in _login_attempts.get(address, []) if now - attempt < LOGIN_WINDOW_SECONDS]
    _login_attempts[address] = attempts
    return len(attempts) >= MAX_LOGIN_ATTEMPTS


def record_login_failure(request: Request):
    now = time.monotonic()
    address = request.client.host if request.client else "unknown"
    _login_attempts.setdefault(address, []).append(now)


def clear_login_failures(request: Request):
    address = request.client.host if request.client else "unknown"
    _login_attempts.pop(address, None)


def verify_app_password(password: str) -> bool:
    expected = os.getenv("FITCHECK_APP_PASSWORD", "")
    return bool(expected) and secrets.compare_digest(password.encode(), expected.encode())


def session_cookie_secure() -> bool:
    return os.getenv("FITCHECK_ENV", "").lower() == "production"
