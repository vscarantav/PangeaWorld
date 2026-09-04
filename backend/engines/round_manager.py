"""Authoritative phase transitions and deterministic round processing."""

from sqlalchemy.orm import Session

try:
    from ..models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Round, RoundStatus
    from ..models.schemas import CompanyDecisionData, PresidentDecisionData
except ImportError:
    from models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Round, RoundStatus
    from models.schemas import CompanyDecisionData, PresidentDecisionData

from .economy import calculate_cpi, calculate_gdp, calculate_inflation, calculate_unemployment
from .resources import produce_resources
from .events import event_effects, generate_round_events


def _current_round(session: GameSession) -> Round:
    current = next((round_ for round_ in session.rounds if round_.number == session.current_round), None)
    if current is None:
        raise ValueError(f"Round {session.current_round} does not exist")
    return current


def _validated_decision(player_type: str, decision_data: dict) -> dict:
    if not isinstance(decision_data, dict):
        raise ValueError("decision_data must be an object")
    schema = PresidentDecisionData if player_type == "president" else CompanyDecisionData
    try:
        return schema.model_validate(decision_data).model_dump(exclude_none=True)
    except Exception as exc:
        # Pydantic's detailed validation is useful to API clients, but the
        # engine exposes one stable exception type to its route layer.
        raise ValueError(f"invalid {player_type} decision: {exc}") from exc


def apply_auto_decisions(entity, player_type: str) -> dict:
    """Return conservative, explicit defaults for a missed submission."""
    if player_type == "president":
        policies = entity.policies or {}
        return {
            "government_spending": 0.0,
            "tax_rate": policies.get("tax_rate", 0.15),
            "tariffs": policies.get("tariffs", 0.05),
            "resource_consumption": {},
            "auto_decision": True,
        }
    if player_type == "company":
        product = (entity.products or {}).get("Widget", {})
        return {
            "price": float(product.get("price", 100.0)),
            "headcount": 0,
            "production_units": 1.0,
            "auto_decision": True,
        }
    raise ValueError("player_type must be 'president' or 'company'")


def submit_decision(db: Session, session: GameSession, player_type: str, entity_id: int, decision_data: dict) -> Decision:
    """Create or replace one validated decision for the active entity/phase."""
    if player_type not in {"president", "company"}:
        raise ValueError("player_type must be 'president' or 'company'")
    expected_phase = PhaseEnum.PRESIDENTIAL if player_type == "president" else PhaseEnum.COMPANY
    if session.phase != expected_phase:
        raise ValueError(f"{player_type} decisions are not accepted during {session.phase.value}")

    entity = None
    if player_type == "president":
        entity = db.query(Nation).filter_by(id=entity_id, session_id=session.id).first()
    else:
        entity = db.query(Company).join(Nation).filter(Company.id == entity_id, Nation.session_id == session.id).first()
    if not entity:
        raise ValueError(f"{player_type} entity does not belong to this session")

    normalized = _validated_decision(player_type, decision_data)
    if player_type == "president" and normalized.get("government_spending", 0.0) > float(entity.treasury or 0.0):
        raise ValueError("government_spending cannot exceed the nation's treasury")

    current_round = _current_round(session)
    decision = db.query(Decision).filter_by(round_id=current_round.id, player_type=player_type, entity_id=entity_id).first()
    if decision is None:
        decision = Decision(round_id=current_round.id, player_type=player_type, entity_id=entity_id)
        db.add(decision)
    decision.decision_data = normalized
    db.commit()
    db.refresh(decision)
    return decision


def _decision_map(current_round: Round) -> dict[tuple[str, int], dict]:
    return {(d.player_type, d.entity_id): (d.decision_data or {}) for d in current_round.decisions}


def _process_company(company: Company, decision: dict, tax_rate: float) -> dict:
    product = dict((company.products or {}).get("Widget", {}))
    old_price = max(0.01, float(product.get("price", 100.0)))
    new_price = old_price if decision.get("price") is None else float(decision["price"])
    volume = max(0.0, float(decision.get("production_units", 1.0)))
    headcount = max(0, int(decision.get("headcount", 0)))
    price_factor = min(1.5, max(0.5, (old_price / max(new_price, 0.01)) ** 0.6))
    staffing_factor = 1.0 + min(headcount, 100) / 1000
    old_revenue = max(0.0, float(company.revenue or 0.0))
    revenue = round(old_revenue * price_factor * volume * staffing_factor, 4)
    old_cogs_ratio = min(0.95, max(0.1, float(company.cogs or 0.0) / old_revenue)) if old_revenue else 0.6
    cogs = round(revenue * old_cogs_ratio, 4)
    gross_profit = max(0.0, revenue - cogs)
    operating_profit = gross_profit * 0.8 - headcount * 0.05
    net_profit = round(operating_profit * (1.0 - tax_rate), 4)
    company.products = {**(company.products or {}), "Widget": {**product, "price": round(new_price, 4)}}
    company.revenue = revenue
    company.cogs = cogs
    company.gross_margin = round((gross_profit / revenue) * 100, 4) if revenue else 0.0
    company.net_profit = net_profit
    company.cash = round(float(company.cash or 0.0) + net_profit, 4)
    return {
        "company_id": company.id,
        "price": new_price,
        "headcount": headcount,
        "revenue": company.revenue,
        "cogs": company.cogs,
        "gross_margin": company.gross_margin,
        "net_profit": company.net_profit,
        "cash": company.cash,
    }


def generate_round_results(session: GameSession, nation_results: list[dict], company_results: list[dict]) -> dict:
    """Build the immutable JSON payload stored on the completed round."""
    return {
        "round": session.current_round,
        "nations": nation_results,
        "companies": company_results,
    }


def process_round(db: Session, session: GameSession) -> dict:
    """Run the authoritative economy/resource loop for the active round."""
    current_round = _current_round(session)
    if session.phase != PhaseEnum.PROCESSING:
        raise ValueError("round can only be processed from the processing phase")
    current_round.status = RoundStatus.PROCESSING
    decisions = _decision_map(current_round)
    current_round.events = generate_round_events(session, current_round)
    nation_results = []
    company_results = []

    for nation in session.nations:
        presidential = decisions.get(("president", nation.id)) or apply_auto_decisions(nation, "president")
        government_spending = float(presidential.get("government_spending", 0.0))
        if government_spending > float(nation.treasury or 0.0):
            raise ValueError("government_spending cannot exceed the nation's treasury")
        nation.policies = {
            **(nation.policies or {}),
            **{key: presidential[key] for key in ("tax_rate", "income_tax", "tariffs", "immigration") if key in presidential},
        }
        previous_cpi = float(nation.cpi or 100.0)
        multipliers, cpi_delta = event_effects(current_round.events or [], nation.id)
        consumption = presidential.get("resource_consumption") or {}
        resource_result = produce_resources(nation, current_round.number, consumption, multipliers)
        resource_demands = {
            getattr(resource.type, "value", resource.type): float(resource.production_rate or 0.0) + float(consumption.get(getattr(resource.type, "value", resource.type), 0.0))
            for resource in nation.resources
        }
        tax_rate = float(nation.policies.get("tax_rate", 0.15))
        for company in nation.companies:
            company_decision = decisions.get(("company", company.id)) or apply_auto_decisions(company, "company")
            company_results.append(_process_company(company, company_decision, tax_rate))
        nation.gdp = round(calculate_gdp(nation, government_spending), 4)
        nation.cpi = round(calculate_cpi(nation, resource_demands) + cpi_delta, 4)
        nation.inflation = calculate_inflation(nation.cpi, previous_cpi)
        labor_pool = sum(float(r.stockpile or 0.0) for r in nation.resources if getattr(r.type, "value", r.type) == "Labor")
        headcount = sum(int((decisions.get(("company", company.id), {}).get("headcount", 0))) for company in nation.companies)
        nation.unemployment = calculate_unemployment(headcount, int(labor_pool)) if labor_pool else float(nation.unemployment or 0.0)
        nation.treasury = round(float(nation.treasury or 0.0) - government_spending, 4)
        total_revenue = sum(float(company.revenue or 0.0) for company in nation.companies)
        for company in nation.companies:
            company.market_share = round((float(company.revenue or 0.0) / total_revenue) * 100, 4) if total_revenue else 0.0
        nation_results.append({
            "nation_id": nation.id,
            "gdp": nation.gdp,
            "cpi": nation.cpi,
            "inflation": nation.inflation,
            "unemployment": nation.unemployment,
            "trade_balance": nation.trade_balance,
            "treasury": nation.treasury,
            "resources": resource_result,
            "events": [event for event in current_round.events if event.get("nation_id") == nation.id],
        })

    current_round.results = generate_round_results(session, nation_results, company_results)
    current_round.status = RoundStatus.COMPLETE
    completed_number = current_round.number
    if completed_number < 7:
        session.current_round = completed_number + 1
        session.phase = PhaseEnum.PLANNING
        db.add(Round(session_id=session.id, number=session.current_round, status=RoundStatus.PLANNING))
    else:
        session.phase = PhaseEnum.COMPLETE
        session.status = "complete"
    db.commit()
    return {"round": completed_number, "status": current_round.status.value, "nations": nation_results, "companies": company_results}


def advance_phase(db: Session, session: GameSession) -> dict:
    """Advance one phase, processing the round after both decision phases."""
    transitions = {PhaseEnum.PLANNING: PhaseEnum.PRESIDENTIAL, PhaseEnum.PRESIDENTIAL: PhaseEnum.COMPANY, PhaseEnum.COMPANY: PhaseEnum.PROCESSING}
    if session.phase in transitions:
        session.phase = transitions[session.phase]
        if session.phase == PhaseEnum.PROCESSING:
            _current_round(session).status = RoundStatus.SUBMITTED
        db.commit()
        return {"phase": session.phase.value, "round": session.current_round, "processed": False}
    if session.phase == PhaseEnum.PROCESSING:
        result = process_round(db, session)
        return {"phase": session.phase.value, "round": session.current_round, "processed": True, "results": result}
    raise ValueError("session has no advanceable phase")
