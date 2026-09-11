from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..auth import get_current_user
    from ..database import get_db
    from ..models.domain import Company, GameMembership, Nation, User
    from ..realtime import notify_session
    from ..engines.ai_backfill import is_backfilled, is_scripted_seat
except ImportError:
    from auth import get_current_user
    from database import get_db
    from models.domain import Company, GameMembership, Nation, User
    from realtime import notify_session
    from engines.ai_backfill import is_backfilled, is_scripted_seat
from .helpers import get_session_or_404, require_instructor

router = APIRouter(prefix="/api/sessions/{session_id}/backfill", tags=["backfill"])


def _seats(session):
    assigned = {(member.role, member.entity_id): member for member in session.memberships if member.entity_id is not None}
    result = []
    for nation in session.nations:
        if not is_scripted_seat(session, nation):
            member = assigned.get(("president", nation.id))
            result.append({"seat_id": f"president:{nation.id}", "role": "president", "entity_id": nation.id, "name": nation.name,
                           "control": "ai" if is_backfilled(session, "president", nation.id) else "human", "user_id": member.user_id if member else None})
        for company in nation.companies:
            if not is_scripted_seat(session, nation):
                member = assigned.get(("executive", company.id))
                result.append({"seat_id": f"executive:{company.id}", "role": "executive", "entity_id": company.id, "name": company.name,
                               "control": "ai" if is_backfilled(session, "executive", company.id) else "human", "user_id": member.user_id if member else None})
    return result


@router.get("/status")
def status(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    eligible = [{"user_id": member.user_id, "display_name": member.user.display_name or member.user.email}
                for member in session.memberships if member.role == "player" and member.entity_id is None]
    return {"seats": _seats(session), "eligible_members": eligible,
            "note": "AI-controlled seats receive the existing conservative automatic allocation until a human takes over."}


class TakeoverRequest(BaseModel):
    user_id: int = Field(gt=0)


@router.post("/{seat_id}/takeover")
def takeover(session_id: int, seat_id: str, payload: TakeoverRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    if session.status != "active": raise HTTPException(status_code=409, detail="AI takeover is available after the game starts")
    try:
        role, raw_id = seat_id.split(":", 1); entity_id = int(raw_id)
    except ValueError as exc: raise HTTPException(status_code=422, detail="seat_id must be role:entity_id") from exc
    if role not in {"president", "executive"}: raise HTTPException(status_code=422, detail="unsupported seat role")
    seat = next((item for item in _seats(session) if item["seat_id"] == seat_id), None)
    if seat is None: raise HTTPException(status_code=404, detail="seat not found or reserved for scripted play")
    if seat["control"] == "human": raise HTTPException(status_code=409, detail="seat is already human-controlled")
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=payload.user_id).first()
    if membership is None or membership.role != "player" or membership.entity_id is not None:
        raise HTTPException(status_code=422, detail="takeover user must be an unassigned member of this game")
    membership.role, membership.entity_id = role, entity_id
    db.commit(); notify_session(session_id, "assignment_changed", membership_id=membership.id)
    return {"seat_id": seat_id, "control": "human", "user_id": membership.user_id}
