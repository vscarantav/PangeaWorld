from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from engines.round_manager import advance_phase
from models.domain import GameSession, PhaseEnum
from seed_data import seed_game_session
from .helpers import get_session_or_404

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    seed: str = "local-dev-seed"

@router.post("")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = GameSession(seed=payload.seed, phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); db.refresh(session)
    seed_game_session(db, session.id)
    return get_session(session.id, db)

@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    return {"id": session.id, "seed": session.seed, "current_round": session.current_round,
            "phase": session.phase.value, "status": session.status, "map_snapshot": session.map_snapshot,
            "rounds": [{"id": r.id, "number": r.number, "status": r.status.value, "events": r.events or []} for r in session.rounds]}

@router.post("/{session_id}/advance")
def advance_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    try:
        return advance_phase(db, session)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
