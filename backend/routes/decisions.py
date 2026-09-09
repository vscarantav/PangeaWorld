from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..engines.round_manager import submit_decision
    from ..models.schemas import CompanyDecisionData, PresidentDecisionData
    from ..models.domain import DecisionDraft, Round, User
    from ..auth import get_current_user
except ImportError:
    from database import get_db
    from engines.round_manager import submit_decision
    from models.schemas import CompanyDecisionData, PresidentDecisionData
    from models.domain import DecisionDraft, Round, User
    from auth import get_current_user
from .helpers import get_session_or_404, require_membership

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["decisions"])

class PresidentDecisionPayload(BaseModel):
    decision_data: PresidentDecisionData = Field(default_factory=PresidentDecisionData)


class CompanyDecisionPayload(BaseModel):
    decision_data: CompanyDecisionData = Field(default_factory=CompanyDecisionData)

def _owned_session(session_id: int, entity_id: int, player_type: str, db: Session, user: User):
    session = get_session_or_404(db, session_id)
    membership = require_membership(db, session_id, user.id)
    expected_role = "president" if player_type == "president" else "executive"
    if membership.role != expected_role or membership.entity_id != entity_id:
        raise HTTPException(status_code=403, detail="you do not own this decision seat")
    return session


def _submit(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    session = _owned_session(session_id, entity_id, player_type, db, user)
    try:
        decision = submit_decision(db, session, player_type, entity_id, payload.decision_data.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
    db.query(DecisionDraft).filter_by(round_id=round_.id, player_type=player_type, entity_id=entity_id).delete()
    db.commit()
    return {"id": decision.id, "round_id": decision.round_id, "player_type": decision.player_type,
            "entity_id": decision.entity_id, "decision_data": decision.decision_data}

@router.post("/nations/{nation_id}/decisions")
def submit_presidential_decision(session_id: int, nation_id: int, payload: PresidentDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _submit(session_id, nation_id, "president", payload, db, user)

@router.post("/companies/{company_id}/decisions")
def submit_company_decision(session_id: int, company_id: int, payload: CompanyDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _submit(session_id, company_id, "company", payload, db, user)


def _save_draft(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    session = _owned_session(session_id, entity_id, player_type, db, user)
    expected_phase = "presidential" if player_type == "president" else "company"
    if session.phase.value != expected_phase:
        raise HTTPException(status_code=409, detail=f"{player_type} drafts are locked during {session.phase.value}")
    round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
    draft = db.query(DecisionDraft).filter_by(round_id=round_.id, player_type=player_type, entity_id=entity_id).first()
    if draft is None:
        draft = DecisionDraft(round_id=round_.id, player_type=player_type, entity_id=entity_id)
        db.add(draft)
    draft.decision_data = payload.decision_data.model_dump(exclude_none=True)
    db.commit(); db.refresh(draft)
    return {"id": draft.id, "round_id": draft.round_id, "status": "draft"}


@router.put("/nations/{nation_id}/draft")
def save_presidential_draft(session_id: int, nation_id: int, payload: PresidentDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _save_draft(session_id, nation_id, "president", payload, db, user)


@router.put("/companies/{company_id}/draft")
def save_company_draft(session_id: int, company_id: int, payload: CompanyDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _save_draft(session_id, company_id, "company", payload, db, user)
