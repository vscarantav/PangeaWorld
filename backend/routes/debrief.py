from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..auth import get_current_user
    from ..database import get_db
    from ..engines.debrief import REAL_WORLD_CONNECTIONS, counterfactual_from_review
    from ..models.domain import Decision, DecisionReview, GameMembership, Round, RoundStatus, User
except ImportError:
    from auth import get_current_user
    from database import get_db
    from engines.debrief import REAL_WORLD_CONNECTIONS, counterfactual_from_review
    from models.domain import Decision, DecisionReview, GameMembership, Round, RoundStatus, User
from .helpers import get_session_or_404, require_assigned_membership

router = APIRouter(prefix="/api/sessions/{session_id}/debrief", tags=["debrief"])


def _completed_session(db, session_id, user):
    session = get_session_or_404(db, session_id)
    member = require_assigned_membership(db, session_id, user.id)
    if session.phase.value != "complete":
        raise HTTPException(status_code=409, detail="debrief is available after the game is complete")
    return session, member


@router.get("/timeline")
def timeline(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session, _member = _completed_session(db, session_id, user)
    timeline_rows = []
    for round_ in sorted(session.rounds, key=lambda item: item.number):
        decisions = [{"role": item.player_type, "entity_id": item.entity_id, "submission_kind": item.submission_kind, "auto_reason": item.auto_reason}
                     for item in round_.decisions]
        timeline_rows.append({"round": round_.number, "status": round_.status.value, "events": round_.events or [],
                              "results": round_.results or {}, "decisions": decisions,
                              "turning_point": any((event.get("impact") == "High" for event in (round_.events or [])))})
    return {"timeline": timeline_rows}


class WhatIfRequest(BaseModel):
    decision_review_id: int = Field(gt=0)


@router.post("/what-if")
def what_if(session_id: int, payload: WhatIfRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _session, member = _completed_session(db, session_id, user)
    review = db.get(DecisionReview, payload.decision_review_id)
    round_ = db.get(Round, review.round_id) if review is not None else None
    if review is None or round_ is None or round_.session_id != session_id:
        raise HTTPException(status_code=404, detail="decision review not found")
    expected_role = "company" if member.role == "executive" else member.role
    if member.role != "instructor" and (review.player_type != expected_role or review.entity_id != member.entity_id):
        raise HTTPException(status_code=403, detail="you may only inspect your own decision counterfactual")
    try:
        return counterfactual_from_review(review)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/connections")
def connections(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session, _member = _completed_session(db, session_id, user)
    observed = set()
    for round_ in session.rounds:
        observed.update(str(event.get("category", "")).lower() for event in (round_.events or []))
        observed.update(str(event.event_type.value) for event in round_.phase3_events)
        observed.update("military_attack" for effect in round_.effects if effect.effect_type == "military_attack")
    return {"connections": [{"event_type": key, **value} for key, value in REAL_WORLD_CONNECTIONS.items() if key in observed]}
