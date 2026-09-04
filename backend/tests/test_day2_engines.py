from types import SimpleNamespace

import pytest

from engines.economy import calculate_cpi, calculate_gdp, calculate_inflation, calculate_trade_balance, calculate_unemployment
from engines.logistics import calculate_landed_cost, estimate_route
from engines.resources import calculate_scarcity, process_trade, produce_resources
from models.domain import ResourceType
from models.domain import GameSession, Nation, PhaseEnum, RoundStatus
from engines.round_manager import _apply_infrastructure_events, advance_phase, process_round, submit_decision
from database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from seed_data import seed_game_session
from engines.events import event_effects, generate_round_events


def nation_fixture():
    return SimpleNamespace(
        cpi=100.0,
        trade_balance=25.0,
        companies=[SimpleNamespace(revenue=100.0), SimpleNamespace(revenue=50.0)],
        resources=[SimpleNamespace(type=ResourceType.ENERGY, stockpile=100.0, production_rate=20.0, depletion_rate=2.0)],
    )


def test_economy_formulas_are_deterministic():
    nation = nation_fixture()
    assert calculate_gdp(nation, government_spending=10) == 185.0
    assert calculate_cpi(nation, {"Energy": 60}) == 150.0
    assert calculate_inflation(105, 100) == 5.0
    assert calculate_unemployment(75, 100) == 25.0
    assert calculate_trade_balance([100, 25], [40]) == 85.0


def test_resource_production_applies_depletion_and_consumption():
    nation = nation_fixture()
    result = produce_resources(nation, consumption={"Energy": 8})
    assert result[0]["after"] == 110.0
    assert nation.resources[0].stockpile == 110.0


def test_scarcity_and_trade():
    exporter = SimpleNamespace(type=ResourceType.MINERALS, stockpile=100.0)
    importer = SimpleNamespace(type=ResourceType.MINERALS, stockpile=10.0)
    scarcity = calculate_scarcity(ResourceType.MINERALS, [exporter, importer], 220)
    assert scarcity["price_multiplier"] == 2.0
    trade = process_trade(exporter, importer, 20, {"base_price": 10, "distance_edges": 2, "mode": "rail"})
    assert trade["total_cost"] == 680.0
    assert exporter.stockpile == 80.0
    assert importer.stockpile == 30.0


def test_landed_cost_modes_and_validation():
    sea = calculate_landed_cost(10, 2, mode="sea")
    rail = calculate_landed_cost(10, 2, mode="rail")
    assert sea["distance_km"] == 200.0
    assert sea["unit_cost"] == 14.0
    assert rail["unit_cost"] == 34.0
    with pytest.raises(ValueError):
        calculate_landed_cost(10, 1, mode="teleport")


def test_map_route_estimates_distance_ports_and_transit():
    snapshot = {
        "countries": [
            {"id": "A", "name": "Alpha", "x": 0, "y": 0},
            {"id": "B", "name": "Beta", "x": 21, "y": 0},
        ],
        "cities": [
            {"country_id": "A", "is_port": True},
            {"country_id": "B", "is_port": True},
        ],
    }
    rail = estimate_route(snapshot, "Alpha", "Beta", "rail")
    assert rail == {"distance_edges": 3, "distance_km": 300, "mode": "rail", "transit_rounds": 1}
    assert estimate_route(snapshot, "Alpha", "Beta", "sea")["transit_rounds"] == 3
    snapshot["cities"][1]["is_port"] = False
    with pytest.raises(ValueError, match="port"):
        estimate_route(snapshot, "Alpha", "Beta", "sea")


def test_round_manager_processes_decisions_and_advances():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="round-seed", phase=PhaseEnum.PLANNING)
    db.add(session)
    db.commit()
    seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()

    advance_phase(db, session)
    submit_decision(db, session, "president", nation.id, {"government_spending": 10})
    advance_phase(db, session)
    company = nation.companies[0]
    submit_decision(db, session, "company", company.id, {"headcount": 20})
    advance_phase(db, session)
    result = advance_phase(db, session)

    assert result["processed"] is True
    assert result["results"]["status"] == RoundStatus.COMPLETE.value
    assert db.get(Nation, nation.id).treasury < 5000.0
    assert session.current_round == 2
    assert session.phase == PhaseEnum.PLANNING


def test_events_are_seeded_and_repeatable():
    session = SimpleNamespace(seed="same-seed", nations=[SimpleNamespace(id=1), SimpleNamespace(id=2)])
    round_ = SimpleNamespace(number=1)
    first = generate_round_events(session, round_)
    second = generate_round_events(session, round_)
    assert first == second
    assert 1 <= len(first) <= 2
    assert all(event["nation_id"] in {1, 2} for event in first)


def test_events_change_approval_and_can_damage_saved_infrastructure():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="event-seed", phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    session.map_snapshot = {
        "countries": [{"id": "TARGET", "name": nation.name}],
        "cities": [{"triangle_id": 10, "country_id": "TARGET"}],
        "edges": [{"id": 99, "triangle_ids": [10, 11], "has_railroad": True}],
    }
    events = [{"nation_id": nation.id, "approval_delta": -3, "damages_infrastructure": True}]
    effects = event_effects(events, nation.id)
    assert effects["approval_delta"] == -3
    _apply_infrastructure_events(session, events)
    assert session.map_snapshot["edges"][0]["has_railroad"] is False
    assert events[0]["infrastructure_damage"]["edge_id"] == 99


def test_three_round_single_nation_walkthrough():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="three-round-seed", phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    company = nation.companies[0]
    for _ in range(3):
        advance_phase(db, session)
        submit_decision(db, session, "president", nation.id, {"government_spending": 10})
        advance_phase(db, session)
        submit_decision(db, session, "company", company.id, {"headcount": 20})
        advance_phase(db, session)
        advance_phase(db, session)
    assert session.current_round == 4
    completed = [round_ for round_ in session.rounds if round_.number <= 3]
    assert len([round_ for round_ in completed if round_.events]) == 3
    for round_ in completed:
        assert round_.status == RoundStatus.COMPLETE
        assert round_.results["nations"]
        assert round_.results["companies"]
        for nation_result in round_.results["nations"]:
            assert nation_result["gdp"] > 0
            assert 50 <= nation_result["cpi"] <= 300
            assert 0 <= nation_result["unemployment"] <= 100
            assert 0 <= nation_result["approval_rating"] <= 100
            assert all(resource["after"] >= 0 for resource in nation_result["resources"])
        assert any(resource["depleted"] > 0 for result in round_.results["nations"] for resource in result["resources"])


def test_decisions_change_company_state_and_policy_state():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="decision-seed", phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    company = nation.companies[0]
    starting_revenue = company.revenue
    advance_phase(db, session)
    submit_decision(db, session, "president", nation.id, {"government_spending": 10, "tax_rate": 0.3})
    advance_phase(db, session)
    starting_quality = company.products["Widget"]["quality"]
    submit_decision(db, session, "company", company.id, {"price": 150, "headcount": 20, "production_units": 1.1, "rnd_investment": 100})
    advance_phase(db, session); advance_phase(db, session)
    db.refresh(nation); db.refresh(company)
    assert nation.policies["tax_rate"] == 0.3
    assert company.products["Widget"]["price"] == 150
    assert company.products["Widget"]["quality"] > starting_quality
    assert company.revenue != starting_revenue
    assert company.market_share > 0


def test_sourcing_executes_trade_and_updates_financials_and_balances():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="trade-seed", phase=PhaseEnum.PLANNING, map_snapshot={
        "countries": [
            {"id": "TERRANOVA", "name": "Terranova", "x": 0, "y": 0},
            {"id": "VALDORIA", "name": "Valdoria", "x": 21, "y": 0},
        ],
        "cities": [],
        "edges": [],
    })
    db.add(session); db.commit(); seed_game_session(db, session.id)
    importer = db.query(Nation).filter_by(session_id=session.id, name="Terranova").one()
    exporter = db.query(Nation).filter_by(session_id=session.id, name="Valdoria").one()
    company = importer.companies[0]
    importer_energy = next(resource for resource in importer.resources if resource.type == ResourceType.ENERGY)
    exporter_energy = next(resource for resource in exporter.resources if resource.type == ResourceType.ENERGY)
    starting_importer_stock = importer_energy.stockpile
    starting_exporter_stock = exporter_energy.stockpile
    starting_cogs = company.cogs

    advance_phase(db, session)
    submit_decision(db, session, "president", importer.id, {})
    advance_phase(db, session)
    submit_decision(db, session, "company", company.id, {
        "price": 150,
        "headcount": 20,
        "production_units": 1.1,
        "rnd_investment": 100,
        "sourcing": [{"resource_type": "Energy", "supplier_nation_id": exporter.id, "quantity": 2, "mode": "rail"}],
    })
    advance_phase(db, session)
    result = advance_phase(db, session)["results"]
    db.refresh(importer); db.refresh(exporter); db.refresh(company)

    company_result = next(item for item in result["companies"] if item["company_id"] == company.id)
    assert company_result["production_units"] == 1.1
    assert company_result["rnd_investment"] == 100
    assert company_result["sourcing"][0]["distance_edges"] == 3
    assert company_result["sourcing_cost"] > 0
    assert company_result["shipping_cost"] > 0
    assert company.cogs != starting_cogs
    assert importer_energy.stockpile >= starting_importer_stock + 2
    assert exporter_energy.stockpile > starting_exporter_stock - 2
    assert importer.trade_balance < 0
    assert exporter.trade_balance > 0
    assert company.supply_chain_config["suppliers"][0]["resource_type"] == "Energy"


def test_overspending_is_rejected():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="budget-seed", phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    advance_phase(db, session)
    with pytest.raises(ValueError, match="treasury"):
        submit_decision(db, session, "president", nation.id, {"government_spending": nation.treasury + 1})


def test_impossible_company_commitments_are_rejected_before_processing():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    session = GameSession(seed="validation-seed", phase=PhaseEnum.PLANNING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    buyer = db.query(Nation).filter_by(session_id=session.id, name="Terranova").one()
    supplier = db.query(Nation).filter_by(session_id=session.id, name="Valdoria").one()
    company = buyer.companies[0]
    advance_phase(db, session)
    advance_phase(db, session)
    with pytest.raises(ValueError, match="cannot be shipped by air"):
        submit_decision(db, session, "company", company.id, {
            "sourcing": [{"resource_type": "Energy", "supplier_nation_id": supplier.id, "quantity": 1, "mode": "air"}],
        })
    with pytest.raises(ValueError, match="R&D"):
        submit_decision(db, session, "company", company.id, {"rnd_investment": company.cash + 1})
