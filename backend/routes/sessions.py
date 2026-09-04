from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..engines.round_manager import advance_phase
    from ..models.domain import GameSession, PhaseEnum
    from ..seed_data import seed_game_session
except ImportError:
    from database import get_db
    from engines.round_manager import advance_phase
    from models.domain import GameSession, PhaseEnum
    from seed_data import seed_game_session
from .helpers import get_session_or_404
try:
    from ..map_snapshots import normalize_map_snapshot
    from ..models.domain import MapSnapshot
except ImportError:
    from map_snapshots import normalize_map_snapshot
    from models.domain import MapSnapshot

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    seed: str = "local-dev-seed"
    map_snapshot: dict | None = Field(default=None)

@router.post("")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = GameSession(seed=payload.seed, phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); db.refresh(session)
    if payload.map_snapshot is not None:
        try:
            snapshot = normalize_map_snapshot(payload.map_snapshot)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if snapshot["seed"] != payload.seed:
            raise HTTPException(status_code=422, detail="map_snapshot.seed must match session seed")
        session.map_snapshot = snapshot
        db.add(MapSnapshot(session_id=session.id, validated_map_json=snapshot))
        db.commit()
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

@router.get("/{session_id}/news")
def get_news(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    articles = []
    for round_ in sorted(session.rounds, key=lambda item: item.number, reverse=True):
        for event in reversed(round_.events or []):
            articles.append({"id": event["id"], "round": round_.number, "headline": event["headline"],
                             "category": event["category"], "impact": event["impact"], "nation_id": event["nation_id"]})
    return {"articles": articles}
