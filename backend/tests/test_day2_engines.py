from types import SimpleNamespace

import pytest

from engines.economy import calculate_cpi, calculate_gdp, calculate_inflation, calculate_trade_balance, calculate_unemployment
from engines.logistics import calculate_landed_cost
from engines.resources import calculate_scarcity, process_trade, produce_resources
from models.domain import ResourceType
from models.domain import GameSession, Nation, PhaseEnum, RoundStatus
from engines.round_manager import advance_phase, process_round, submit_decision
from database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from seed_data import seed_game_session
from engines.events import generate_round_events


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
    assert calculate_cpi(nation, {"Energy": 60}) == 50.0
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
    assert len([round_ for round_ in session.rounds if round_.number <= 3 and round_.events]) == 3
