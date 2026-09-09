"""Password hashing and cookie-session dependencies for the local multiplayer MVP."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
import hmac
import os
import secrets

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

try:
    from .database import get_db
    from .models.domain import AuthSession, User
except ImportError:  # Allows ``uvicorn main:app`` from inside backend.
    from database import get_db
    from models.domain import AuthSession, User


SESSION_COOKIE = "pangeaworld_session"
PASSWORD_ITERATIONS = 310_000
SESSION_DAYS = 7


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(
        (
            "pbkdf2_sha256",
            str(PASSWORD_ITERATIONS),
            urlsafe_b64encode(salt).decode("ascii"),
            urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_text, digest_text = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = urlsafe_b64decode(salt_text.encode("ascii"))
        expected = urlsafe_b64decode(digest_text.encode("ascii"))
        actual = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def _token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """SQLite can return timezone-aware columns as naive datetimes."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def create_auth_session(db: Session, user: User, response: Response, revoke_existing: bool = False) -> AuthSession:
    if revoke_existing:
        db.query(AuthSession).filter_by(user_id=user.id, revoked_at=None).update({"revoked_at": _utc_now()})
    raw_token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(days=SESSION_DAYS)
    session = AuthSession(user_id=user.id, token_hash=_token_hash(raw_token), expires_at=expires_at)
    db.add(session)
    db.commit()
    db.refresh(session)
    response.set_cookie(
        SESSION_COOKIE,
        raw_token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        expires=expires_at,
        httponly=True,
        secure=os.getenv("PANGEAWORLD_COOKIE_SECURE", "0") == "1",
        samesite="lax",
        path="/",
    )
    return session


def get_auth_session(request: Request, db: Session = Depends(get_db)) -> AuthSession:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    session = db.query(AuthSession).filter_by(token_hash=_token_hash(raw_token), revoked_at=None).first()
    if session is None or _as_utc(session.expires_at) <= _utc_now():
        if session is not None:
            session.revoked_at = _utc_now()
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return session


def get_current_user(auth_session: AuthSession = Depends(get_auth_session)) -> User:
    return auth_session.user
