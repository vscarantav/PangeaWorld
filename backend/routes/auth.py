"""Authentication endpoints for Phase 2's local multiplayer slice."""

from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from ..auth import create_auth_session, get_auth_session, get_current_user, hash_password, verify_password
    from ..database import get_db
    from ..models.domain import AuthSession, User
except ImportError:  # Allows ``uvicorn main:app`` from inside backend.
    from auth import create_auth_session, get_auth_session, get_current_user, hash_password, verify_password
    from database import get_db
    from models.domain import AuthSession, User


router = APIRouter(prefix="/api/auth", tags=["auth"])
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterPayload(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be a valid address")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


def _public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "created_at": user.created_at}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload, response: Response, db: Session = Depends(get_db)):
    user = User(email=payload.email, password_hash=hash_password(payload.password), display_name=payload.display_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already registered") from exc
    db.refresh(user)
    create_auth_session(db, user, response)
    return {"user": _public_user(user)}


@router.post("/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    create_auth_session(db, user, response)
    return {"user": _public_user(user)}


@router.post("/logout")
def logout(response: Response, auth_session: AuthSession = Depends(get_auth_session), db: Session = Depends(get_db)):
    auth_session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    response.delete_cookie("pangeaworld_session", path="/")
    return {"logged_out": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"user": _public_user(user)}
