from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..engines.round_manager import submit_decision
    from ..models.schemas import CompanyDecisionData, PresidentDecisionData
except ImportError:
    from database import get_db
    from engines.round_manager import submit_decision
    from models.schemas import CompanyDecisionData, PresidentDecisionData
from .helpers import get_session_or_404

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["decisions"])

class PresidentDecisionPayload(BaseModel):
    decision_data: PresidentDecisionData = Field(default_factory=PresidentDecisionData)


class CompanyDecisionPayload(BaseModel):
    decision_data: CompanyDecisionData = Field(default_factory=CompanyDecisionData)

def _submit(session_id: int, entity_id: int, player_type: str, payload, db: Session):
    session = get_session_or_404(db, session_id)
    try:
        decision = submit_decision(db, session, player_type, entity_id, payload.decision_data.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": decision.id, "round_id": decision.round_id, "player_type": decision.player_type,
            "entity_id": decision.entity_id, "decision_data": decision.decision_data}

@router.post("/nations/{nation_id}/decisions")
def submit_presidential_decision(session_id: int, nation_id: int, payload: PresidentDecisionPayload, db: Session = Depends(get_db)):
    return _submit(session_id, nation_id, "president", payload, db)

@router.post("/companies/{company_id}/decisions")
def submit_company_decision(session_id: int, company_id: int, payload: CompanyDecisionPayload, db: Session = Depends(get_db)):
    return _submit(session_id, company_id, "company", payload, db)
