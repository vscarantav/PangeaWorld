from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..engines.logistics import calculate_landed_cost, estimate_route
    from ..engines.resources import BASE_PRICES, calculate_scarcity
    from ..models.domain import Company, Nation, Resource, ResourceType, User
    from ..auth import get_current_user
except ImportError:
    from database import get_db
    from engines.logistics import calculate_landed_cost, estimate_route
    from engines.resources import BASE_PRICES, calculate_scarcity
    from models.domain import Company, Nation, Resource, ResourceType, User
    from auth import get_current_user
from .helpers import get_session_or_404, require_assigned_membership

router = APIRouter(prefix="/api/sessions/{session_id}/market", tags=["market"])

@router.get("")
def get_market(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id)
    require_assigned_membership(db, session_id, user.id)
    rows = db.query(Resource).join(Resource.nation).filter(Resource.nation.has(session_id=session_id)).all()
    resources = {}
    for name, price in BASE_PRICES.items():
        matching = [r for r in rows if getattr(r.type, "value", r.type) == name]
        scarcity = calculate_scarcity(name, matching, sum(float(r.production_rate or 0.0) for r in matching))
        resources[name] = {"base_price": price, "global_stockpile": scarcity["supply"], "demand": scarcity["demand"],
                           "price_multiplier": scarcity["price_multiplier"], "current_price": round(price * scarcity["price_multiplier"], 4)}
    return {"resources": resources,
            "shipping_index": 1.0}

@router.get("/resources/{resource_type}")
def get_resource_market(
    session_id: int,
    resource_type: str,
    buyer_nation_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session_or_404(db, session_id)
    membership = require_assigned_membership(db, session_id, user.id)
    if resource_type not in BASE_PRICES:
        raise HTTPException(status_code=404, detail="resource type not found")
    buyer = None
    if buyer_nation_id is not None:
        buyer = db.query(Nation).filter_by(id=buyer_nation_id, session_id=session_id).first()
        if buyer is None:
            raise HTTPException(status_code=404, detail="buyer nation not found")
        if membership.role == "president" and membership.entity_id != buyer_nation_id:
            raise HTTPException(status_code=403, detail="buyer nation must be your assigned nation")
        if membership.role == "executive":
            company = db.query(Company).filter_by(id=membership.entity_id).first()
            if company is None or company.nation_id != buyer_nation_id:
                raise HTTPException(status_code=403, detail="buyer nation must be your company's nation")
    rows = db.query(Resource).join(Resource.nation).filter(Resource.type == ResourceType(resource_type), Resource.nation.has(session_id=session_id)).all()
    scarcity = calculate_scarcity(resource_type, rows, sum(float(r.production_rate or 0.0) for r in rows))
    current_price = BASE_PRICES[resource_type] * scarcity["price_multiplier"]
    suppliers = []
    for resource in rows:
        if float(resource.stockpile or 0.0) <= 0:
            continue
        destination = buyer or resource.nation
        routes = []
        for mode in ("sea", "river", "rail", "air"):
            if resource_type == "Energy" and mode == "air":
                continue
            try:
                route = estimate_route(session.map_snapshot, resource.nation.name, destination.name, mode)
            except ValueError:
                continue
            foreign = resource.nation_id != destination.id
            cost = calculate_landed_cost(
                current_price,
                route["distance_edges"],
                mode,
                tariff_rate=float((destination.policies or {}).get("tariffs", 0.0)) if foreign else 0.0,
                insurance_rate=0.02 if foreign else 0.0,
                port_fees=2.0 if mode == "sea" else 0.0,
            )
            routes.append({**route, **cost})
        rail = next((route for route in routes if route["mode"] == "rail"), None)
        suppliers.append({
            "nation_id": resource.nation_id,
            "nation_name": resource.nation.name,
            "stockpile": resource.stockpile,
            "routes": routes,
            "estimated_rail_unit_cost": rail["unit_cost"] if rail else None,
        })
    return {"resource_type": resource_type, "suppliers": suppliers,
            "base_price": BASE_PRICES[resource_type], "price_multiplier": scarcity["price_multiplier"], "current_price": round(current_price, 4)}
