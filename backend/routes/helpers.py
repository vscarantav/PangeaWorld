from fastapi import HTTPException
from sqlalchemy.orm import Session

try:
    from ..models.domain import Company, GameMembership, GameSession, Nation
except ImportError:
    from models.domain import Company, GameMembership, GameSession, Nation


def get_session_or_404(db: Session, session_id: int) -> GameSession:
    session = db.query(GameSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="game session not found")
    return session


def require_membership(db: Session, session_id: int, user_id: int) -> GameMembership:
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=user_id).first()
    if membership is None:
        raise HTTPException(status_code=403, detail="not a member of this game")
    return membership


def require_instructor(db: Session, session_id: int, user_id: int) -> GameMembership:
    membership = require_membership(db, session_id, user_id)
    if membership.role != "instructor":
        raise HTTPException(status_code=403, detail="instructor role required")
    return membership


def require_assigned_membership(db: Session, session_id: int, user_id: int) -> GameMembership:
    membership = require_membership(db, session_id, user_id)
    if membership.role not in {"instructor", "president", "executive"}:
        raise HTTPException(status_code=403, detail="an assigned game seat is required")
    if membership.role != "instructor" and membership.entity_id is None:
        raise HTTPException(status_code=403, detail="an assigned game seat is required")
    return membership


def can_read_nation(db: Session, membership: GameMembership, nation_id: int) -> bool:
    if membership.role in {"instructor", "president"}:
        return membership.role == "instructor" or membership.entity_id == nation_id
    company = db.query(Company).filter_by(id=membership.entity_id).first()
    return membership.role == "executive" and company is not None and company.nation_id == nation_id


def can_read_company(db: Session, membership: GameMembership, company_id: int) -> bool:
    if membership.role == "instructor": return True
    if membership.role == "executive": return membership.entity_id == company_id
    company = db.query(Company).filter_by(id=company_id).first()
    return membership.role == "president" and company is not None and company.nation_id == membership.entity_id


def serialize_company(company) -> dict:
    return {"id": company.id, "nation_id": company.nation_id, "name": company.name, "revenue": company.revenue,
            "cogs": company.cogs, "gross_margin": company.gross_margin, "net_profit": company.net_profit,
            "cash": company.cash, "market_share": company.market_share, "products": company.products or {},
            "supply_chain_config": company.supply_chain_config or {}}


def serialize_nation(nation, include_companies: bool = True) -> dict:
    data = {"id": nation.id, "session_id": nation.session_id, "name": nation.name, "archetype": nation.archetype,
            "gdp": nation.gdp, "cpi": nation.cpi, "inflation": nation.inflation, "unemployment": nation.unemployment,
            "approval_rating": nation.approval_rating,
            "trade_balance": nation.trade_balance, "treasury": nation.treasury, "military_atk": nation.military_atk,
            "military_def": nation.military_def, "military_readiness": nation.military_readiness,
            "emergency_preparedness_balance": nation.emergency_preparedness_balance,
            "military_inventory": nation.military_inventory or {}, "policies": nation.policies or {},
            "resources": [{"id": r.id, "type": getattr(r.type, "value", r.type), "production_rate": r.production_rate,
                           "stockpile": r.stockpile, "depletion_rate": r.depletion_rate} for r in nation.resources]}
    if include_companies:
        data["companies"] = [serialize_company(company) for company in nation.companies]
    return data
