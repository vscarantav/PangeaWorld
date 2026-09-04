from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models.domain import Company, Nation
except ImportError:
    from database import get_db
    from models.domain import Company, Nation
from .helpers import get_session_or_404, serialize_company

router = APIRouter(prefix="/api/sessions/{session_id}/companies", tags=["companies"])

@router.get("")
def list_companies(session_id: int, db: Session = Depends(get_db)):
    get_session_or_404(db, session_id)
    return [serialize_company(c) for c in db.query(Company).join(Nation).filter(Nation.session_id == session_id).all()]

@router.get("/{company_id}")
def get_company(session_id: int, company_id: int, db: Session = Depends(get_db)):
    get_session_or_404(db, session_id)
    company = db.query(Company).join(Nation).filter(Company.id == company_id, Nation.session_id == session_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="company not found")
    return serialize_company(company)
