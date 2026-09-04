from fastapi import HTTPException
from sqlalchemy.orm import Session

try:
    from ..models.domain import GameSession
except ImportError:
    from models.domain import GameSession


def get_session_or_404(db: Session, session_id: int) -> GameSession:
    session = db.query(GameSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="game session not found")
    return session


def serialize_company(company) -> dict:
    return {"id": company.id, "nation_id": company.nation_id, "name": company.name, "revenue": company.revenue,
            "cogs": company.cogs, "gross_margin": company.gross_margin, "net_profit": company.net_profit,
            "cash": company.cash, "market_share": company.market_share, "products": company.products or {},
            "supply_chain_config": company.supply_chain_config or {}}


def serialize_nation(nation, include_companies: bool = True) -> dict:
    data = {"id": nation.id, "session_id": nation.session_id, "name": nation.name, "archetype": nation.archetype,
            "gdp": nation.gdp, "cpi": nation.cpi, "inflation": nation.inflation, "unemployment": nation.unemployment,
            "trade_balance": nation.trade_balance, "treasury": nation.treasury, "military_atk": nation.military_atk,
            "military_def": nation.military_def, "policies": nation.policies or {},
            "resources": [{"id": r.id, "type": getattr(r.type, "value", r.type), "production_rate": r.production_rate,
                           "stockpile": r.stockpile, "depletion_rate": r.depletion_rate} for r in nation.resources]}
    if include_companies:
        data["companies"] = [serialize_company(company) for company in nation.companies]
    return data
