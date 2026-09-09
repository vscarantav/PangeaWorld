from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models.domain import Company, Nation, User
    from ..auth import get_current_user
except ImportError:
    from database import get_db
    from models.domain import Company, Nation, User
    from auth import get_current_user
from .helpers import can_read_company, get_session_or_404, require_assigned_membership, serialize_company

router = APIRouter(prefix="/api/sessions/{session_id}/companies", tags=["companies"])

@router.get("")
def list_companies(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id)
    membership = require_assigned_membership(db, session_id, user.id)
    rows = db.query(Company).join(Nation).filter(Nation.session_id == session_id).all()
    return [serialize_company(c) for c in rows if can_read_company(db, membership, c.id)]

@router.get("/{company_id}")
def get_company(session_id: int, company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id)
    membership = require_assigned_membership(db, session_id, user.id)
    company = db.query(Company).join(Nation).filter(Company.id == company_id, Nation.session_id == session_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="company not found")
    if not can_read_company(db, membership, company_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="you do not have access to this company")
    return serialize_company(company)
