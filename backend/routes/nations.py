from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.domain import Nation
from .helpers import get_session_or_404, serialize_nation

router = APIRouter(prefix="/api/sessions/{session_id}/nations", tags=["nations"])

@router.get("")
def list_nations(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    return [serialize_nation(nation, include_companies=False) for nation in session.nations]

@router.get("/{nation_id}")
def get_nation(session_id: int, nation_id: int, db: Session = Depends(get_db)):
    get_session_or_404(db, session_id)
    nation = db.query(Nation).filter_by(id=nation_id, session_id=session_id).first()
    if not nation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="nation not found")
    return serialize_nation(nation)
