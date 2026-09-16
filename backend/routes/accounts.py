"""Installation-level account roles and role-aware landing dashboard."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from ..auth import get_current_user, hash_password
    from ..database import get_db
    from ..models.domain import GameMembership, GameSession, User
except ImportError:
    from auth import get_current_user, hash_password
    from database import get_db
    from models.domain import GameMembership, GameSession, User


router = APIRouter(prefix="/api/accounts", tags=["accounts"])
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ACCOUNT_TYPES = {"admin", "professor", "student"}


class ManagedUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    account_type: str = Field(default="student", pattern="^(professor|student)$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be a valid address")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class RoleUpdate(BaseModel):
    account_type: str = Field(pattern="^(admin|professor|student)$")


def _account_type(user: User) -> str:
    return user.account_type if user.account_type in ACCOUNT_TYPES else ("professor" if user.is_instructor else "student")


def _user_view(user: User) -> dict:
    role = _account_type(user)
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "account_type": role,
        "managed_by_user_id": user.managed_by_user_id,
        "created_at": user.created_at,
    }


def _require_staff(user: User) -> str:
    role = _account_type(user)
    if role not in {"admin", "professor"}:
        raise HTTPException(status_code=403, detail="professor or admin account required")
    return role


def _session_view(session: GameSession, user_id: int) -> dict:
    assigned = [item for item in session.memberships if item.role in {"president", "executive"} and item.entity_id]
    owner = next((item.user for item in session.memberships if item.user_id == session.owner_user_id), None)
    return {
        "id": session.id,
        "status": session.status,
        "phase": getattr(session.phase, "value", session.phase),
        "current_round": session.current_round,
        "created_at": session.created_at,
        "join_code": None if session.lobby_code_revoked else session.lobby_join_code,
        "member_count": len(session.memberships),
        "assigned_seats": len(assigned),
        "owner_user_id": session.owner_user_id,
        "owner_name": (owner.display_name or owner.email) if owner else "Legacy session",
        "is_member": any(item.user_id == user_id for item in session.memberships),
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = _account_type(user)
    if role == "admin":
        users = db.query(User).order_by(User.created_at.desc(), User.id.desc()).all()
        sessions = db.query(GameSession).order_by(GameSession.created_at.desc(), GameSession.id.desc()).all()
    elif role == "professor":
        users = db.query(User).filter_by(account_type="student", managed_by_user_id=user.id).order_by(User.created_at.desc(), User.id.desc()).all()
        legacy_ids = [item.session_id for item in db.query(GameMembership).filter_by(user_id=user.id, role="instructor").all()]
        sessions = db.query(GameSession).filter(
            (GameSession.owner_user_id == user.id) | (GameSession.id.in_(legacy_ids or [-1]))
        ).order_by(GameSession.created_at.desc(), GameSession.id.desc()).all()
    else:
        users = []
        session_ids = [item.session_id for item in db.query(GameMembership).filter_by(user_id=user.id).all()]
        sessions = db.query(GameSession).filter(GameSession.id.in_(session_ids or [-1])).order_by(
            GameSession.created_at.desc(), GameSession.id.desc()
        ).all()

    counts = {name: db.query(User).filter_by(account_type=name).count() for name in ACCOUNT_TYPES} if role == "admin" else {}
    return {
        "account_type": role,
        "counts": counts,
        "users": [_user_view(item) for item in users],
        "sessions": [_session_view(item, user.id) for item in sessions],
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_managed_user(payload: ManagedUserCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    actor_role = _require_staff(user)
    if actor_role == "professor" and payload.account_type != "student":
        raise HTTPException(status_code=403, detail="professors can create student accounts only")
    created = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        account_type=payload.account_type,
        is_instructor=1 if payload.account_type == "professor" else 0,
        managed_by_user_id=user.id,
    )
    db.add(created)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="email is already registered") from exc
    db.refresh(created)
    return {"user": _user_view(created)}


@router.patch("/users/{user_id}/role")
def update_role(user_id: int, payload: RoleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if _account_type(user) != "admin":
        raise HTTPException(status_code=403, detail="admin account required")
    target = db.query(User).filter_by(id=user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    if target.id == user.id and payload.account_type != "admin" and db.query(User).filter_by(account_type="admin").count() == 1:
        raise HTTPException(status_code=409, detail="the installation must retain at least one admin")
    target.account_type = payload.account_type
    target.is_instructor = 1 if payload.account_type in {"admin", "professor"} else 0
    db.commit()
    db.refresh(target)
    return {"user": _user_view(target)}


@router.post("/sessions/{session_id}/access")
def claim_admin_session_access(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Let an Admin explicitly enter any session as a facilitator."""
    if _account_type(user) != "admin":
        raise HTTPException(status_code=403, detail="admin account required")
    session = db.query(GameSession).filter_by(id=session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="game session not found")
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=user.id).first()
    if membership is None:
        membership = GameMembership(session_id=session_id, user_id=user.id, role="instructor")
        db.add(membership)
        db.commit()
    return {"session_id": session_id, "membership_id": membership.id}
