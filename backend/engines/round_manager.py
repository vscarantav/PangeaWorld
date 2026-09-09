"""Authoritative phase transitions and deterministic round processing."""

from copy import deepcopy

from sqlalchemy.orm import Session

try:
    from ..models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Resource, Round, RoundStatus
    from ..models.schemas import CompanyDecisionData, PresidentDecisionData
except ImportError:
    from models.domain import Company, Decision, GameSession, Nation, PhaseEnum, Resource, Round, RoundStatus
    from models.schemas import CompanyDecisionData, PresidentDecisionData

from .economy import calculate_cpi, calculate_gdp, calculate_inflation, calculate_unemployment
from .events import event_effects, generate_round_events
from .logistics import calculate_landed_cost, estimate_route
from .resources import BASE_PRICES, calculate_scarcity, process_trade, produce_resources


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
            "rnd_investment": 0.0,
            "sourcing": [],
            "auto_decision": True,
        }
    raise ValueError("player_type must be 'president' or 'company'")


def _validate_company_sourcing(db: Session, session: GameSession, company: Company, decision: dict) -> None:
    """Reject impossible orders while the company can still edit its decision."""
    rnd_investment = float(decision.get("rnd_investment", 0.0))
    if rnd_investment > float(company.cash or 0.0):
        raise ValueError("R&D investment cannot exceed company cash")
    resources = db.query(Resource).join(Nation).filter(Nation.session_id == session.id).all()
    reserved_stock = {}
    estimated_total = rnd_investment
    for order in decision.get("sourcing") or []:
        resource_type = getattr(order.get("resource_type"), "value", order.get("resource_type"))
        mode = str(order.get("mode", "rail")).lower()
        if resource_type == "Energy" and mode == "air":
            raise ValueError("Energy cannot be shipped by air")
        supplier = next((resource for resource in resources if resource.nation_id == int(order["supplier_nation_id"]) and getattr(resource.type, "value", resource.type) == resource_type), None)
        if supplier is None:
            raise ValueError(f"supplier does not offer {resource_type} in this session")
        stock_key = (supplier.nation_id, resource_type)
        reserved_stock[stock_key] = reserved_stock.get(stock_key, 0.0) + float(order["quantity"])
        if reserved_stock[stock_key] > float(supplier.stockpile or 0.0):
            raise ValueError(f"supplier only has {float(supplier.stockpile or 0.0):.2f} units of {resource_type}")
        matching = [resource for resource in resources if getattr(resource.type, "value", resource.type) == resource_type]
        demand = sum(float(resource.production_rate or 0.0) for resource in matching)
        scarcity = calculate_scarcity(resource_type, matching, demand)
        market_price = BASE_PRICES[resource_type] * float(scarcity["price_multiplier"])
        route = estimate_route(session.map_snapshot, supplier.nation.name, company.nation.name, mode)
        foreign = supplier.nation_id != company.nation_id
        preview = calculate_landed_cost(
            market_price,
            route["distance_edges"],
            mode,
            tariff_rate=float((company.nation.policies or {}).get("tariffs", 0.0)) if foreign else 0.0,
            insurance_rate=0.02 if foreign else 0.0,
            port_fees=2.0 if mode == "sea" else 0.0,
        )
        estimated_total += float(preview["unit_cost"]) * float(order["quantity"])
    if estimated_total > float(company.cash or 0.0):
        raise ValueError(f"R&D and sourcing commitments (${estimated_total:.2f}) cannot exceed company cash")


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
    if player_type == "company":
        _validate_company_sourcing(db, session, entity, normalized)

    current_round = _current_round(session)
    decision = db.query(Decision).filter_by(round_id=current_round.id, player_type=player_type, entity_id=entity_id).first()
    if decision is None:
        decision = Decision(round_id=current_round.id, player_type=player_type, entity_id=entity_id)
        db.add(decision)
    decision.decision_data = normalized
    decision.submission_kind = "human"
    decision.auto_reason = None
    db.commit()
    db.refresh(decision)
    return decision


def _decision_map(current_round: Round) -> dict[tuple[str, int], dict]:
    return {(d.player_type, d.entity_id): (d.decision_data or {}) for d in current_round.decisions}


def _process_company(company: Company, decision: dict, tax_rate: float, sourcing: list[dict]) -> dict:
    product = dict((company.products or {}).get("Widget", {}))
    old_price = max(0.01, float(product.get("price", 100.0)))
    new_price = old_price if decision.get("price") is None else float(decision["price"])
    volume = max(0.0, float(decision.get("production_units", 1.0)))
    headcount = max(0, int(decision.get("headcount", 0)))
    rnd_investment = max(0.0, float(decision.get("rnd_investment", 0.0)))
    price_factor = min(1.5, max(0.5, (old_price / max(new_price, 0.01)) ** 0.6))
    staffing_factor = 1.0 + min(headcount, 100) / 1000
    old_revenue = max(0.0, float(company.revenue or 0.0))
    revenue = round(old_revenue * price_factor * volume * staffing_factor, 4)
    old_cogs_ratio = min(0.95, max(0.1, float(company.cogs or 0.0) / old_revenue)) if old_revenue else 0.6
    sourcing_cost = round(sum(float(order["total_cost"]) for order in sourcing), 4)
    shipping_cost = round(sum(float(order["shipping_cost"]) for order in sourcing), 4)
    cogs = round(revenue * old_cogs_ratio + sourcing_cost, 4)
    gross_profit = revenue - cogs
    operating_profit = gross_profit * 0.8 - headcount * 0.05 - rnd_investment
    net_profit = round(operating_profit * (1.0 - tax_rate), 4) if operating_profit > 0 else round(operating_profit, 4)
    quality = round(float(product.get("quality", 5.0)) + rnd_investment / 10000.0, 4)
    company.products = {**(company.products or {}), "Widget": {**product, "price": round(new_price, 4), "production_units": volume, "quality": quality}}
    company.revenue = revenue
    company.cogs = cogs
    company.gross_margin = round((gross_profit / revenue) * 100, 4) if revenue else 0.0
    company.net_profit = net_profit
    company.cash = round(float(company.cash or 0.0) + net_profit, 4)
    company.supply_chain_config = {"suppliers": sourcing, "updated_round": decision.get("round_number")}
    return {
        "company_id": company.id,
        "price": new_price,
        "headcount": headcount,
        "production_units": volume,
        "rnd_investment": rnd_investment,
        "quality": quality,
        "revenue": company.revenue,
        "cogs": company.cogs,
        "sourcing_cost": sourcing_cost,
        "shipping_cost": shipping_cost,
        "sourcing": sourcing,
        "gross_margin": company.gross_margin,
        "net_profit": company.net_profit,
        "cash": company.cash,
    }


def _process_sourcing(session: GameSession, company: Company, orders: list[dict], resources: list[Resource], available_cash: float | None = None) -> list[dict]:
    """Validate and execute a company's resource orders at round-time prices."""
    completed = []
    committed_cost = 0.0
    for order in orders:
        resource_type = getattr(order.get("resource_type"), "value", order.get("resource_type"))
        mode = str(order.get("mode", "rail")).lower()
        if resource_type == "Energy" and mode == "air":
            raise ValueError("Energy cannot be shipped by air")
        supplier = next((resource for resource in resources if resource.nation_id == int(order["supplier_nation_id"]) and getattr(resource.type, "value", resource.type) == resource_type), None)
        importer = next((resource for resource in company.nation.resources if getattr(resource.type, "value", resource.type) == resource_type), None)
        if supplier is None or importer is None:
            completed.append({"resource_type": resource_type, "supplier_nation_id": order.get("supplier_nation_id"), "quantity": 0.0, "requested_quantity": float(order["quantity"]), "mode": mode, "status": "unfilled", "total_cost": 0.0, "shipping_cost": 0.0})
            continue
        matching = [resource for resource in resources if getattr(resource.type, "value", resource.type) == resource_type]
        demand = sum(float(resource.production_rate or 0.0) for resource in matching)
        scarcity = calculate_scarcity(resource_type, matching, demand)
        market_price = BASE_PRICES[resource_type] * float(scarcity["price_multiplier"])
        route = estimate_route(session.map_snapshot, supplier.nation.name, company.nation.name, mode)
        foreign = supplier.nation_id != company.nation_id
        route_cost = {
            "base_price": market_price,
            "distance_edges": route["distance_edges"],
            "mode": mode,
            "tariff_rate": float((company.nation.policies or {}).get("tariffs", 0.0)) if foreign else 0.0,
            "insurance_rate": 0.02 if foreign else 0.0,
            "port_fees": 2.0 if mode == "sea" else 0.0,
        }
        preview = calculate_landed_cost(**route_cost)
        requested_quantity = float(order["quantity"])
        cash_limit = float(company.cash or 0.0) if available_cash is None else available_cash
        affordable_quantity = max(0.0, (cash_limit - committed_cost) / float(preview["unit_cost"]))
        quantity = min(requested_quantity, float(supplier.stockpile or 0.0), affordable_quantity)
        if quantity <= 0:
            completed.append({"resource_type": resource_type, "supplier_nation_id": supplier.nation_id, "quantity": 0.0, "requested_quantity": requested_quantity, "mode": mode, "status": "unfilled", "total_cost": 0.0, "shipping_cost": 0.0})
            continue
        trade = process_trade(supplier, importer, quantity, route_cost)
        committed_cost += float(trade["total_cost"])
        if foreign:
            supplier.nation.trade_balance = round(float(supplier.nation.trade_balance or 0.0) + float(trade["total_cost"]), 4)
            company.nation.trade_balance = round(float(company.nation.trade_balance or 0.0) - float(trade["total_cost"]), 4)
        breakdown = trade["cost_breakdown"]
        completed.append({
            "resource_type": resource_type,
            "supplier_nation_id": supplier.nation_id,
            "quantity": trade["quantity"],
            "requested_quantity": requested_quantity,
            "status": "filled" if quantity == requested_quantity else "partially_filled",
            "mode": mode,
            "distance_edges": route["distance_edges"],
            "distance_km": route["distance_km"],
            "transit_rounds": route["transit_rounds"],
            "unit_cost": trade["unit_cost"],
            "total_cost": trade["total_cost"],
            "shipping_cost": round((float(breakdown["freight"]) + float(breakdown["insurance"]) + float(breakdown["port_fees"])) * trade["quantity"], 4),
            "tariff_cost": round(float(breakdown["tariffs"]) * trade["quantity"], 4),
        })
    return completed


def _apply_infrastructure_events(session: GameSession, events: list[dict]) -> None:
    """Persist deterministic railroad damage for infrastructure events."""
    if not session.map_snapshot or not any(event.get("damages_infrastructure") for event in events):
        return
    snapshot = deepcopy(session.map_snapshot)
    countries = {country.get("name"): country for country in snapshot.get("countries", [])}
    nations = {nation.id: nation for nation in session.nations}
    changed = False
    for event in events:
        if not event.get("damages_infrastructure"):
            continue
        nation = nations.get(event.get("nation_id"))
        country = countries.get(nation.name) if nation else None
        if not country:
            continue
        city_triangles = {
            city.get("triangle_id") for city in snapshot.get("cities", [])
            if str(city.get("country_id")) == str(country.get("id"))
        }
        candidates = [
            edge for edge in snapshot.get("edges", [])
            if edge.get("has_railroad") and city_triangles.intersection(edge.get("triangle_ids", []))
        ]
        if candidates:
            damaged = sorted(candidates, key=lambda edge: str(edge.get("id")))[0]
            damaged["has_railroad"] = False
            event["infrastructure_damage"] = {"edge_id": damaged.get("id"), "type": "railroad", "nation": nation.name}
            changed = True
    if changed:
        session.map_snapshot = snapshot
        for stored in session.map_snapshots:
            stored.validated_map_json = snapshot


def generate_round_results(session: GameSession, nation_results: list[dict], company_results: list[dict]) -> dict:
    """Build the immutable JSON payload stored on the completed round."""
    return {
        "round": session.current_round,
        "nations": nation_results,
        "companies": company_results,
    }


def process_round(db: Session, session: GameSession, commit: bool = True) -> dict:
    """Run the authoritative economy/resource loop for the active round."""
    current_round = _current_round(session)
    if session.phase != PhaseEnum.PROCESSING:
        raise ValueError("round can only be processed from the processing phase")
    current_round.status = RoundStatus.PROCESSING
    decisions = _decision_map(current_round)
    current_round.events = generate_round_events(session, current_round)
    nation_results = []
    company_results = []
    nation_state = {}
    all_resources = db.query(Resource).join(Nation).filter(Nation.session_id == session.id).all()

    # Produce resources and apply public policy/event effects before companies
    # compete for the same round's available stock.
    for nation in session.nations:
        nation.trade_balance = 0.0
        presidential = decisions.get(("president", nation.id)) or apply_auto_decisions(nation, "president")
        government_spending = float(presidential.get("government_spending", 0.0))
        if government_spending > float(nation.treasury or 0.0):
            raise ValueError("government_spending cannot exceed the nation's treasury")
        nation.policies = {
            **(nation.policies or {}),
            **{key: presidential[key] for key in ("tax_rate", "income_tax", "tariffs", "immigration") if key in presidential},
        }
        previous_cpi = float(nation.cpi or 100.0)
        effects = event_effects(current_round.events or [], nation.id)
        consumption = presidential.get("resource_consumption") or {}
        resource_result = produce_resources(nation, current_round.number, consumption, effects["production_multipliers"])
        resource_demands = {
            getattr(resource.type, "value", resource.type): float(resource.production_rate or 0.0) + float(consumption.get(getattr(resource.type, "value", resource.type), 0.0))
            for resource in nation.resources
        }
        nation.approval_rating = round(min(100.0, max(0.0, float(nation.approval_rating or 60.0) + effects["approval_delta"])), 4)
        nation.treasury = round(float(nation.treasury or 0.0) - government_spending, 4)
        nation_state[nation.id] = {
            "presidential": presidential,
            "government_spending": government_spending,
            "previous_cpi": previous_cpi,
            "cpi_delta": effects["cpi_delta"],
            "resource_result": resource_result,
            "resource_demands": resource_demands,
        }

    _apply_infrastructure_events(session, current_round.events)

    # Execute every sourcing order and feed its landed cost into the owning
    # company's financial results.
    for nation in session.nations:
        tax_rate = float(nation.policies.get("tax_rate", 0.15))
        for company in nation.companies:
            company_decision = decisions.get(("company", company.id)) or apply_auto_decisions(company, "company")
            rnd_investment = float(company_decision.get("rnd_investment", 0.0))
            if rnd_investment > float(company.cash or 0.0):
                raise ValueError(f"company {company.id} cannot afford its R&D investment")
            sourcing = _process_sourcing(session, company, company_decision.get("sourcing") or [], all_resources, float(company.cash or 0.0) - rnd_investment)
            company_results.append(_process_company(company, {**company_decision, "round_number": current_round.number}, tax_rate, sourcing))

    # Market share is global because all companies sell into the same virtual
    # consumer market.
    all_companies = [company for nation in session.nations for company in nation.companies]
    global_revenue = sum(float(company.revenue or 0.0) for company in all_companies)
    company_result_by_id = {result["company_id"]: result for result in company_results}
    for company in all_companies:
        company.market_share = round((float(company.revenue or 0.0) / global_revenue) * 100, 4) if global_revenue else 0.0
        company_result_by_id[company.id]["market_share"] = company.market_share

    for nation in session.nations:
        state = nation_state[nation.id]
        nation.gdp = round(calculate_gdp(nation, state["government_spending"]), 4)
        nation.cpi = round(calculate_cpi(nation, state["resource_demands"]) + state["cpi_delta"], 4)
        nation.inflation = calculate_inflation(nation.cpi, state["previous_cpi"])
        labor_pool = sum(float(r.stockpile or 0.0) for r in nation.resources if getattr(r.type, "value", r.type) == "Labor")
        headcount = sum(int((decisions.get(("company", company.id), {}).get("headcount", 0))) for company in nation.companies)
        nation.unemployment = calculate_unemployment(headcount, int(labor_pool)) if labor_pool else float(nation.unemployment or 0.0)
        for resource_result in state["resource_result"]:
            current_resource = next(resource for resource in nation.resources if getattr(resource.type, "value", resource.type) == resource_result["type"])
            resource_result["after"] = current_resource.stockpile
        nation_results.append({
            "nation_id": nation.id,
            "gdp": nation.gdp,
            "cpi": nation.cpi,
            "inflation": nation.inflation,
            "unemployment": nation.unemployment,
            "approval_rating": nation.approval_rating,
            "trade_balance": nation.trade_balance,
            "treasury": nation.treasury,
            "resources": state["resource_result"],
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
    if commit:
        db.commit()
    return {"round": completed_number, "status": current_round.status.value, "nations": nation_results, "companies": company_results}


def advance_phase(db: Session, session: GameSession, commit: bool = True) -> dict:
    """Advance one phase, processing the round after both decision phases."""
    transitions = {PhaseEnum.PLANNING: PhaseEnum.PRESIDENTIAL, PhaseEnum.PRESIDENTIAL: PhaseEnum.COMPANY, PhaseEnum.COMPANY: PhaseEnum.PROCESSING}
    if session.phase in transitions:
        session.phase = transitions[session.phase]
        if session.phase == PhaseEnum.PROCESSING:
            _current_round(session).status = RoundStatus.SUBMITTED
        if commit:
            db.commit()
        return {"phase": session.phase.value, "round": session.current_round, "processed": False}
    if session.phase == PhaseEnum.PROCESSING:
        result = process_round(db, session, commit=commit)
        return {"phase": session.phase.value, "round": session.current_round, "processed": True, "results": result}
    raise ValueError("session has no advanceable phase")
