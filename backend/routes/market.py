from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..engines.logistics import calculate_landed_cost
    from ..models.domain import Resource, ResourceType
except ImportError:
    from database import get_db
    from engines.logistics import calculate_landed_cost
    from models.domain import Resource, ResourceType
from .helpers import get_session_or_404

router = APIRouter(prefix="/api/sessions/{session_id}/market", tags=["market"])
BASE_PRICES = {"Energy": 40.0, "Minerals": 60.0, "Agriculture": 30.0, "Technology": 100.0, "Labor": 25.0, "Capital": 80.0}

@router.get("")
def get_market(session_id: int, db: Session = Depends(get_db)):
    get_session_or_404(db, session_id)
    rows = db.query(Resource).join(Resource.nation).filter(Resource.nation.has(session_id=session_id)).all()
    return {"resources": {name: {"base_price": price, "global_stockpile": round(sum(r.stockpile for r in rows if getattr(r.type, "value", r.type) == name), 4)}
                           for name, price in BASE_PRICES.items()},
            "shipping_index": 1.0}

@router.get("/resources/{resource_type}")
def get_resource_market(session_id: int, resource_type: str, db: Session = Depends(get_db)):
    get_session_or_404(db, session_id)
    if resource_type not in BASE_PRICES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="resource type not found")
    rows = db.query(Resource).join(Resource.nation).filter(Resource.type == ResourceType(resource_type), Resource.nation.has(session_id=session_id)).all()
    return {"resource_type": resource_type, "suppliers": [{"nation_id": r.nation_id, "stockpile": r.stockpile,
             "estimated_rail_unit_cost": calculate_landed_cost(BASE_PRICES[resource_type], 1, "rail")["unit_cost"]} for r in rows]}
