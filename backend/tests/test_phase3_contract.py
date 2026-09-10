import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from models.domain import (
    Company, CompanyRecoveryFunding, Decision, EventScope, EventType, GameSession,
    MilitaryPosture, Nation, PhaseEnum, Round, RoundEffect, RoundEvent,
)
from models.schemas import PresidentDecisionData
from engines.round_manager import process_round, submit_decision
from engines.phase3_contract import validate_event_severity, validate_event_target
from engines.phase3_resolver import resolve_natural_disaster
from seed_data import seed_game_session
from main import app
from tests.test_authorization import setup_game


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_president_phase3_inputs_are_typed_and_bounded():
    decision = PresidentDecisionData(
        military_posture=MilitaryPosture.PATROL,
        military_investment=250.0,
        emergency_preparedness_investment=400.0,
    )
    assert decision.model_dump()["military_posture"] == "patrol"
    assert decision.emergency_preparedness_investment == 400.0

    with pytest.raises(ValidationError):
        PresidentDecisionData(military_posture="attack")
    with pytest.raises(ValidationError):
        PresidentDecisionData(emergency_preparedness_investment=-1)


def test_phase3_event_effect_and_recovery_records_are_round_scoped():
    db = make_db()
    session = GameSession(seed="phase3-contract")
    db.add(session); db.commit(); seed_game_session(db, session.id)
    round_ = db.query(Round).filter_by(session_id=session.id, number=1).one()
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    company = db.query(Company).filter_by(nation_id=nation.id).first()

    event = RoundEvent(
        round_id=round_.id,
        event_type=EventType.NATURAL_DISASTER,
        target_nation_id=nation.id,
        severity=2,
        event_data={"catalog_key": "coastal_storm", "seed": "phase3-contract:1"},
    )
    db.add(event); db.flush()
    funding = CompanyRecoveryFunding(
        round_event_id=event.id,
        company_id=company.id,
        public_fund_amount=100.0,
        private_fund_amount=50.0,
        private_financing_cost=15.0,
    )
    effect = RoundEffect(
        round_id=round_.id,
        round_event_id=event.id,
        entity_type="nation",
        entity_id=nation.id,
        effect_type="disaster_recovery",
        scope=EventScope.PUBLIC,
        effect_data={"gdp_delta": -25.0, "approval_delta": -2.0},
        reproducibility_key="phase3-contract:1:coastal_storm",
    )
    db.add_all([funding, effect]); db.commit(); db.refresh(round_)

    assert round_.phase3_events[0].recovery_funding[0].private_financing_cost == 15.0
    assert round_.effects[0].effect_data["gdp_delta"] == -25.0

    db.add(CompanyRecoveryFunding(round_event_id=event.id, company_id=company.id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_phase3_presidential_commitments_share_the_existing_treasury_limit():
    db = make_db()
    session = GameSession(seed="phase3-budget", phase=PhaseEnum.PRESIDENTIAL)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    nation.treasury = 100.0
    db.commit()

    with pytest.raises(ValueError, match="emergency investments"):
        submit_decision(db, session, "president", nation.id, {
            "government_spending": 40.0,
            "military_investment": 30.0,
            "emergency_preparedness_investment": 40.0,
        })


def test_phase3_event_contract_rejects_foreign_targets_and_invalid_severity():
    db = make_db()
    first = GameSession(seed="phase3-first")
    second = GameSession(seed="phase3-second")
    db.add_all([first, second]); db.commit()
    seed_game_session(db, first.id); seed_game_session(db, second.id)
    first_round = db.query(Round).filter_by(session_id=first.id, number=1).one()
    foreign_nation = db.query(Nation).filter_by(session_id=second.id).first()

    with pytest.raises(ValueError, match="does not belong"):
        validate_event_target(db, first_round, EventType.NATURAL_DISASTER, foreign_nation.id)
    with pytest.raises(ValueError, match="severity"):
        validate_event_severity(4)
    assert validate_event_severity(2) == 2


def test_phase3_readiness_api_enforces_identity_phase_and_budget():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    try:
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}).status_code == 200
        guest = TestClient(app)
        payload = {"decision_data": {
            "military_posture": "patrol",
            "military_investment": 100.0,
            "emergency_preparedness_investment": 200.0,
        }}
        endpoint = f"/api/sessions/{game_id}/nations/{nation_id}/readiness"
        assert guest.put(endpoint, json=payload).status_code == 401
        assert executive.put(endpoint, json=payload).status_code == 403
        assert president.put(endpoint, json={"decision_data": {"military_posture": "attack"}}).status_code == 422
        saved = president.put(endpoint, json=payload)
        assert saved.status_code == 200
        assert saved.json()["decision_data"]["military_posture"] == "patrol"
        policy = president.post(
            f"/api/sessions/{game_id}/nations/{nation_id}/decisions",
            json={"decision_data": {"government_spending": 250.0, "tax_rate": 0.24}},
        )
        assert policy.status_code == 200
        assert policy.json()["decision_data"]["emergency_preparedness_investment"] == 200.0
        assert policy.json()["decision_data"]["military_posture"] == "patrol"
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}).status_code == 200
        assert president.put(endpoint, json=payload).status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_phase3_instructor_event_api_is_catalog_bound_and_deduplicated():
    instructor, president, _, game_id, nation_id, _ = setup_game()
    try:
        endpoint = f"/api/sessions/{game_id}/phase3"
        assert president.get(f"{endpoint}/event-catalog").status_code == 403
        catalog = instructor.get(f"{endpoint}/event-catalog")
        assert catalog.status_code == 200
        assert {event["key"] for event in catalog.json()} == {"coastal_storm", "major_earthquake"}
        assert instructor.post(f"{endpoint}/events", json={"catalog_key": "unknown", "target_nation_id": nation_id}).status_code == 422
        created = instructor.post(f"{endpoint}/events", json={"catalog_key": "coastal_storm", "target_nation_id": nation_id})
        assert created.status_code == 200
        assert created.json()["target_nation_id"] == nation_id
        assert instructor.post(f"{endpoint}/events", json={"catalog_key": "coastal_storm", "target_nation_id": nation_id}).status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_phase3_disaster_resolver_is_repeatable_and_public_funds_go_first():
    inputs = {
        "event_id": 4, "event_key": "coastal_storm", "severity": 2,
        "nation_id": 7, "posture": "defend", "military_investment": 200.0,
        "public_fund_available": 300.0, "company_ids": [9, 2, 5], "round_number": 3,
    }
    first = resolve_natural_disaster(**inputs)
    assert first == resolve_natural_disaster(**inputs)
    assert first["public_fund_used"] == 300.0
    assert first["private_recovery_total"] > 0
    assert [entry["company_id"] for entry in first["allocations"]] == [2, 5, 9]
    assert sum(entry["private_fund_amount"] for entry in first["allocations"]) == first["private_recovery_total"]


def test_phase3_processing_persists_recovery_effects_exactly_once():
    db = make_db()
    session = GameSession(seed="phase3-resolver", phase=PhaseEnum.PROCESSING)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    round_ = db.query(Round).filter_by(session_id=session.id, number=1).one()
    nation = db.query(Nation).filter_by(session_id=session.id).first()
    nation.treasury = 2_000.0
    db.add(Decision(round_id=round_.id, player_type="president", entity_id=nation.id, decision_data={
        "military_posture": "defend", "military_investment": 200.0,
        "emergency_preparedness_investment": 300.0,
    }))
    event = RoundEvent(round_id=round_.id, event_type=EventType.NATURAL_DISASTER, target_nation_id=nation.id,
                       severity=2, event_data={"catalog_key": "coastal_storm"})
    db.add(event); db.commit()

    result = process_round(db, session, commit=False)
    db.flush()
    assert result["nations"][0]["phase3_effect"]["public_fund_used"] == 300.0
    assert db.query(CompanyRecoveryFunding).filter_by(round_event_id=event.id).count() == len(nation.companies)
    effect = db.query(RoundEffect).filter_by(round_event_id=event.id, entity_type="nation").one()
    assert effect.reproducibility_key.startswith(f"phase3:1:{event.id}:coastal_storm")
    with pytest.raises(ValueError, match="processing phase"):
        process_round(db, session, commit=False)


def test_phase3_results_are_public_deterministic_and_do_not_expose_private_recovery():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    try:
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}).status_code == 200
        readiness = {"decision_data": {"military_posture": "defend", "military_investment": 200.0, "emergency_preparedness_investment": 300.0}}
        assert president.put(f"/api/sessions/{game_id}/nations/{nation_id}/readiness", json=readiness).status_code == 200
        assert president.post(f"/api/sessions/{game_id}/nations/{nation_id}/decisions", json={"decision_data": {"government_spending": 20.0}}).status_code == 200
        assert instructor.post(f"/api/sessions/{game_id}/phase3/events", json={"catalog_key": "coastal_storm", "target_nation_id": nation_id}).status_code == 200
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}).status_code == 200
        assert executive.post(f"/api/sessions/{game_id}/companies/{company_id}/decisions", json={"decision_data": {}}).status_code == 200
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "company"}).status_code == 200
        assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "processing"}).status_code == 200
        first = president.get(f"/api/sessions/{game_id}/phase3/results")
        second = executive.get(f"/api/sessions/{game_id}/phase3/results")
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        result = first.json()["results"][0]
        assert result["article"]["id"] == f"phase3-{result['event_id']}"
        assert "private_financing_cost" not in str(result)
        assert "military_posture" not in str(result)
    finally:
        app.dependency_overrides.clear()
