"""Authoritative phase transitions and single-round simulation orchestration."""

from sqlalchemy.orm import Session

try:
    from ..models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Round, RoundStatus
except ImportError:
    from models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Round, RoundStatus
from .economy import calculate_cpi, calculate_gdp, calculate_inflation, calculate_unemployment
from .resources import produce_resources
from .events import event_effects, generate_round_events


def _current_round(session: GameSession) -> Round:
    current = next((round_ for round_ in session.rounds if round_.number == session.current_round), None)
    if current is None:
        raise ValueError(f"Round {session.current_round} does not exist")
    return current


def submit_decision(db: Session, session: GameSession, player_type: str, entity_id: int, decision_data: dict) -> Decision:
    """Create or replace one decision for the active entity and phase."""
    if player_type not in {"president", "company"}:
        raise ValueError("player_type must be 'president' or 'company'")
    expected_phase = PhaseEnum.PRESIDENTIAL if player_type == "president" else PhaseEnum.COMPANY
    if session.phase != expected_phase:
        raise ValueError(f"{player_type} decisions are not accepted during {session.phase.value}")
    if player_type == "president" and not db.query(Nation).filter_by(id=entity_id, session_id=session.id).first():
        raise ValueError("nation does not belong to this session")
    if player_type == "company":
        company = db.query(Company).join(Nation).filter(Company.id == entity_id, Nation.session_id == session.id).first()
        if not company:
            raise ValueError("company does not belong to this session")
    current_round = _current_round(session)
    decision = db.query(Decision).filter_by(round_id=current_round.id, player_type=player_type, entity_id=entity_id).first()
    if decision is None:
        decision = Decision(round_id=current_round.id, player_type=player_type, entity_id=entity_id)
        db.add(decision)
    decision.decision_data = decision_data
    db.commit()
    db.refresh(decision)
    return decision


def process_round(db: Session, session: GameSession) -> dict:
    """Run the deterministic economy/resource loop for the active round."""
    current_round = _current_round(session)
    if session.phase != PhaseEnum.PROCESSING:
        raise ValueError("round can only be processed from the processing phase")
    decisions = {(d.player_type, d.entity_id): (d.decision_data or {}) for d in current_round.decisions}
    current_round.events = generate_round_events(session, current_round)
    results = []
    for nation in session.nations:
        presidential = decisions.get(("president", nation.id), {})
        government_spending = max(0.0, float(presidential.get("government_spending", 0.0)))
        previous_cpi = float(nation.cpi or 100.0)
        multipliers, cpi_delta = event_effects(current_round.events or [], nation.id)
        resource_result = produce_resources(nation, current_round.number, presidential.get("resource_consumption"), multipliers)
        nation.gdp = round(calculate_gdp(nation, government_spending), 4)
        nation.cpi = round(calculate_cpi(nation) + cpi_delta, 4)
        nation.inflation = calculate_inflation(nation.cpi, previous_cpi)
        labor_pool = sum(float(r.stockpile) for r in nation.resources if getattr(r.type, "value", r.type) == "Labor")
        headcount = sum(int((decisions.get(("company", company.id), {}).get("headcount", 0))) for company in nation.companies)
        nation.unemployment = calculate_unemployment(headcount, int(labor_pool)) if labor_pool else float(nation.unemployment or 0.0)
        nation.treasury = round(nation.treasury - government_spending, 4)
        results.append({"nation_id": nation.id, "gdp": nation.gdp, "cpi": nation.cpi, "inflation": nation.inflation, "resources": resource_result,
                        "events": [event for event in current_round.events if event.get("nation_id") == nation.id]})
    current_round.status = RoundStatus.COMPLETE
    completed_number = current_round.number
    if completed_number < 7:
        session.current_round = completed_number + 1
        session.phase = PhaseEnum.PLANNING
        db.add(Round(session_id=session.id, number=session.current_round, status=RoundStatus.PLANNING))
    else:
        session.phase = PhaseEnum.COMPLETE
    db.commit()
    return {"round": completed_number, "status": current_round.status.value, "nations": results}


def advance_phase(db: Session, session: GameSession) -> dict:
    """Advance one phase, processing the round when both decision phases finish."""
    transitions = {
        PhaseEnum.PLANNING: PhaseEnum.PRESIDENTIAL,
        PhaseEnum.PRESIDENTIAL: PhaseEnum.COMPANY,
        PhaseEnum.COMPANY: PhaseEnum.PROCESSING,
    }
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
