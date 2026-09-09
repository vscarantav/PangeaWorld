from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models.domain import Nation, User
    from ..auth import get_current_user
except ImportError:
    from database import get_db
    from models.domain import Nation, User
    from auth import get_current_user
from .helpers import can_read_nation, get_session_or_404, require_assigned_membership, serialize_nation

router = APIRouter(prefix="/api/sessions/{session_id}/nations", tags=["nations"])

@router.get("")
def list_nations(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    require_assigned_membership(db, session_id, user.id)
    return [serialize_nation(nation, include_companies=False) for nation in session.nations]

@router.get("/{nation_id}")
def get_nation(session_id: int, nation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id)
    membership = require_assigned_membership(db, session_id, user.id)
    nation = db.query(Nation).filter_by(id=nation_id, session_id=session_id).first()
    if not nation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="nation not found")
    if not can_read_nation(db, membership, nation_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="you do not have access to this nation")
    # Executives may inspect their own nation's macro conditions but never the
    # financials or supply-chain settings of sibling companies.
    return serialize_nation(nation, include_companies=membership.role != "executive")
