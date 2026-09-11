from types import SimpleNamespace

from engines.events import event_schedule, generate_round_events


def test_seven_year_event_schedule_and_stable_targets():
    slots = event_schedule("closure")
    assert len(slots) == 14
    assert sum(slot["scale"] == "major" for slot in slots) == 3
    assert sum(slot["scale"] == "minor" for slot in slots) == 11
    assert {slot["round"] for slot in slots} == set(range(1, 8))
    nations = [SimpleNamespace(id=2, cpi=100), SimpleNamespace(id=1, cpi=100)]
    session = SimpleNamespace(ruleset_version="phase3-closure-v1", seed="closure", nations=nations, rounds=[])
    first = [event for year in range(1, 8) for event in generate_round_events(session, SimpleNamespace(number=year))]
    session.nations.reverse()
    assert first == [event for year in range(1, 8) for event in generate_round_events(session, SimpleNamespace(number=year))]


def test_reactive_unrest_uses_prior_state_and_has_one_round_cooldown():
    nation = SimpleNamespace(id=1, cpi=116)
    session = SimpleNamespace(ruleset_version="phase3-closure-v1", seed="reactive", nations=[nation], rounds=[])
    events = generate_round_events(session, SimpleNamespace(number=1))
    assert len([event for event in events if event["source"] == "reactive"]) == 1
    session.rounds = [SimpleNamespace(number=1, events=events)]
    assert not any(event["source"] == "reactive" for event in generate_round_events(session, SimpleNamespace(number=2)))

import json
import pytest
import httpx
from engines.news import generate_news
from engines.round_manager import preview_decision, submit_decision, process_round
from engines.opportunity_cost import RULESET
from engines.phase3_military import apply_strategic_control, resolve_battle
from models.domain import GameSession, Nation, Company, PhaseEnum, Round, DecisionReview, Decision, RoundEffect, EventScope
from seed_data import seed_game_session
from tests.test_phase3_contract import make_db


def closure_game():
    db = make_db()
    session = GameSession(seed="closure-integration", phase=PhaseEnum.PRESIDENTIAL, ruleset_version=RULESET)
    db.add(session); db.commit(); seed_game_session(db, session.id)
    return db, session


def reviewed(db, session, role, entity, data):
    preview = preview_decision(db, session, role, entity, data)
    return {**data, "opportunity_cost": {"preview_token": preview["preview_token"],
        "alternative_id": preview["alternatives"][0]["id"],
        "rationale": "I prioritize this allocation over the next-best alternative because the next unit supports recovery while other investment can wait."}}


def test_review_is_required_feasible_fresh_and_append_only():
    db, session = closure_game()
    nation = session.nations[0]
    with pytest.raises(ValueError, match="compare alternatives"):
        submit_decision(db, session, "president", nation.id, {"government_spending": 100})
    data = reviewed(db, session, "president", nation, {"government_spending": 100})
    with pytest.raises(ValueError, match="refresh the comparison"):
        submit_decision(db, session, "president", nation.id, {**data, "government_spending": 200})
    submit_decision(db, session, "president", nation.id, data)
    original = db.query(DecisionReview).one().record
    submit_decision(db, session, "president", nation.id, reviewed(db, session, "president", nation, {"government_spending": 200}))
    assert db.query(Decision).count() == 1
    assert db.query(DecisionReview).count() == 2
    assert db.query(DecisionReview).order_by(DecisionReview.id).first().record == original
    assert len(original["alternatives"]) >= 2
    assert all(item["commitment"] <= nation.treasury for item in original["alternatives"])


def test_company_capacity_and_working_capital_compete_with_research():
    db, session = closure_game(); session.phase = PhaseEnum.COMPANY
    company = session.nations[0].companies[0]
    with pytest.raises(ValueError, match="capacity"):
        preview_decision(db, session, "company", company, {"production_units": 100})
    with pytest.raises(ValueError, match="commitments"):
        preview_decision(db, session, "company", company, {"production_units": 2, "rnd_investment": company.cash})
    submit_decision(db, session, "company", company.id, reviewed(db, session, "company", company, {"production_units": 1, "rnd_investment": 100}))
    assert db.query(DecisionReview).one().record["assumptions"]["committed"] > 100


def test_eight_nations_complete_seven_rounds_with_persisted_backfill(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db, session = closure_game()
    for year in range(1, 8):
        session.phase = PhaseEnum.PROCESSING
        process_round(db, session)
        assert all(value >= 0 for nation in session.nations for value in nation.military_inventory.values())
    assert session.phase == PhaseEnum.COMPLETE
    assert len(session.rounds) == 7
    assert db.query(Decision).count() == 7 * (8 + 80)
    assert all(round_.results.get("news") for round_ in session.rounds)
    assert db.query(RoundEffect).filter_by(effect_type="intelligence_report", scope=EventScope.PRIVATE).count() == 1
    assert db.query(RoundEffect).filter_by(effect_type="military_attack").count() > 0
    with pytest.raises(ValueError, match="processing phase"):
        process_round(db, session)


def test_gemini_receives_only_public_facts_and_falls_back_safely(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")
    monkeypatch.setenv("GEMINI_NEWS_MODEL", "configured-model")
    nation = {"nation_id": 1, "gdp": 100, "cpi": 105, "inflation": 5, "trade_balance": 0, "private_decision": "secret"}
    seen = []
    def fake_post(url, **kwargs):
        seen.append(kwargs)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "Recorded consumer prices reached 105."}]}}]}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    article = generate_news(1, [nation], [])[0]
    assert article["generation"] == "gemini"
    assert "private_decision" not in json.dumps(seen[0]["json"])
    assert "test-secret" not in json.dumps(article)
    def failed(*args, **kwargs):
        raise httpx.ConnectError("unavailable")
    monkeypatch.setattr(httpx, "post", failed)
    assert generate_news(1, [nation], [])[0]["generation"] == "provider_unavailable_fallback"


def test_multi_engagement_battle_is_repeatable_and_conserves_units():
    inputs = dict(session_seed="retreat", round_number=1, attacker_id=1, target_id=2,
        deployment={"infantry": 6}, attacker_inventory={"infantry": 8}, defender_inventory={"infantry": 12},
        attacker_atk=1, defender_def=10, engagement_limit=3, retreat_threshold=0.4)
    first = resolve_battle(**inputs)
    assert first == resolve_battle(**inputs)
    assert 1 <= first["engagements"] <= 3
    assert sum(first["attacker_inventory_after"].values()) + first["attacker_losses"] == 8
    assert sum(first["defender_inventory_after"].values()) + first["defender_losses"] == 12


def test_victory_transfers_one_strategic_zone_without_erasing_a_nation():
    attacker = SimpleNamespace(policies={"strategic_control_points": 3})
    defender = SimpleNamespace(policies={"strategic_control_points": 2})
    transfer = apply_strategic_control(attacker, defender, "attacker_victory")
    assert transfer["control_transferred"] == 1
    assert attacker.policies["strategic_control_points"] == 4
    assert defender.policies["strategic_control_points"] == 1
    second = apply_strategic_control(attacker, defender, "attacker_victory")
    assert second["control_transferred"] == 0
    assert defender.policies["strategic_control_points"] == 1


def test_failed_attack_does_not_transfer_strategic_control():
    attacker = SimpleNamespace(policies={})
    defender = SimpleNamespace(policies={})
    result = apply_strategic_control(attacker, defender, "defender_holds")
    assert result["control_transferred"] == 0
    assert attacker.policies["strategic_control_points"] == 3
    assert defender.policies["strategic_control_points"] == 3

from main import app
from tests.test_authorization import setup_game


def test_review_api_privacy_and_private_intelligence():
    instructor, president, executive, session_id, nation_id, company_id = setup_game(RULESET)
    try:
        target_id = next(n["id"] for n in instructor.get(f"/api/sessions/{session_id}/nations").json() if n["id"] != nation_id)
        assert instructor.post(f"/api/sessions/{session_id}/advance", json={"expected_phase": "planning"}).status_code == 200
        data = {"military_operation": {"operation_type": "intelligence", "target_nation_id": target_id, "units": {"infantry": 1}}}
        endpoint = f"/api/sessions/{session_id}/decision-review/president/{nation_id}"
        assert executive.post(endpoint, json={"decision_data": data}).status_code == 403
        preview = president.post(endpoint, json={"decision_data": data, "readiness_only": True})
        assert preview.status_code == 200, preview.text
        body = preview.json()
        evidence = {"preview_token": body["preview_token"], "alternative_id": "reserve", "rationale": "I value information now over retaining cash because the next round's investment can wait."}
        assert president.put(f"/api/sessions/{session_id}/nations/{nation_id}/readiness", json={"decision_data": {**data, "opportunity_cost": evidence}}).status_code == 200
        reviews_url = f"/api/sessions/{session_id}/phase3/decision-reviews"
        assert len(president.get(reviews_url).json()["reviews"]) == 1
        assert executive.get(reviews_url).json()["reviews"] == []
        assert len(instructor.get(reviews_url).json()["reviews"]) == 1
        scorecard = instructor.get(f"/api/sessions/{session_id}/phase3/opportunity-cost-scorecard")
        assert scorecard.status_code == 200
        assert scorecard.json()["scorecards"][0]["constraint_recognition_rate"] == 1
        assert executive.get(f"/api/sessions/{session_id}/phase3/opportunity-cost-scorecard").status_code == 403
        for phase in ["presidential", "company", "processing"]:
            if phase == "company":
                submit_review_api(executive, session_id, "company", company_id)
            assert instructor.post(f"/api/sessions/{session_id}/advance", json={"expected_phase": phase}).status_code == 200
        private = president.get(reviews_url).json()
        assert len(private["intelligence_reports"]) == 1
        assert private["reviews"][0]["feedback"] is not None
        assert executive.get(reviews_url).json()["intelligence_reports"] == []
        public = executive.get(f"/api/sessions/{session_id}").json()
        assert "rationale" not in json.dumps(public)
        assert "intelligence_report" not in json.dumps(public)
    finally:
        app.dependency_overrides.clear()


def test_review_preview_is_phase_locked():
    instructor, president, executive, session_id, nation_id, company_id = setup_game(RULESET)
    try:
        endpoint = f"/api/sessions/{session_id}/decision-review/president/{nation_id}"
        assert president.post(endpoint, json={"decision_data": {"government_spending": 10}}).status_code == 409
        assert instructor.post(f"/api/sessions/{session_id}/advance", json={"expected_phase": "planning"}).status_code == 200
        assert president.post(endpoint, json={"decision_data": {"government_spending": 10}}).status_code == 200
        company_endpoint = f"/api/sessions/{session_id}/decision-review/company/{company_id}"
        assert executive.post(company_endpoint, json={"decision_data": {}}).status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_instructor_custom_scenario_and_behavior_controls():
    instructor, president, executive, session_id, nation_id, company_id = setup_game(RULESET)
    try:
        settings = f"/api/sessions/{session_id}/phase3/settings"
        assert president.put(settings, json={"drakmoor_mode": "passive"}).status_code == 403
        assert instructor.put(settings, json={"drakmoor_mode": "passive"}).status_code == 200
        endpoint = f"/api/sessions/{session_id}/phase3/events"
        scenario = {"catalog_key": "custom", "target_nation_id": nation_id, "scenario": {"event_type": "market_shock", "title": "Local price shock", "summary": "A supply squeeze raises consumer prices.", "cpi_delta": 4, "approval_delta": -2}}
        assert instructor.post(endpoint, json=scenario).status_code == 200
        assert instructor.post(endpoint, json=scenario).status_code == 409
        for phase in ["planning", "presidential", "company"]:
            if phase == "presidential":
                submit_review_api(president, session_id, "president", nation_id)
            if phase == "company":
                submit_review_api(executive, session_id, "company", company_id)
            assert instructor.post(f"/api/sessions/{session_id}/advance", json={"expected_phase": phase}).status_code == 200
        assert instructor.post(endpoint, json=scenario).status_code == 409
        assert instructor.post(f"/api/sessions/{session_id}/advance", json={"expected_phase": "processing"}).status_code == 200
        news = president.get(f"/api/sessions/{session_id}/news").json()
        assert any(article["headline"] == "Local price shock" for article in news["articles"])
    finally:
        app.dependency_overrides.clear()


def test_blockade_stops_sea_stock_transfer_and_charges_mission():
    from models.domain import Resource
    from engines.round_manager import _process_sourcing
    db, session = closure_game()
    attacker, target = session.nations[:2]
    company = target.companies[0]
    resource = next(item for item in attacker.resources if item.stockpile > 0)
    # Route geometry is tested separately; this check isolates authoritative
    # shipment suppression and proves no inventory is removed.
    import engines.round_manager as manager
    original_route = manager.estimate_route
    manager.estimate_route = lambda *args: {"distance_edges": 1, "distance_km": 10, "transit_rounds": 0}
    try:
        before = resource.stockpile
        rows = _process_sourcing(session, company, [{"resource_type": resource.type.value,
            "supplier_nation_id": attacker.id, "quantity": 1, "mode": "sea"}],
            db.query(Resource).all(), blockaded={target.id})
        assert rows[0]["status"] == "blockaded"
        assert rows[0]["total_cost"] == 0
        assert resource.stockpile == before
        data = {"military_operation": {"operation_type": "blockade", "target_nation_id": target.id, "units": {"navy": 1}}}
        before_treasury = attacker.treasury
        submit_decision(db, session, "president", attacker.id, reviewed(db, session, "president", attacker, data))
        session.phase = PhaseEnum.PROCESSING
        process_round(db, session)
        assert attacker.treasury == before_treasury - 50
    finally:
        manager.estimate_route = original_route


def submit_review_api(client, session_id, role, entity_id):
    data = {"government_spending": 100} if role == "president" else {"production_units": 1, "rnd_investment": 100}
    preview = client.post(f"/api/sessions/{session_id}/decision-review/{role}/{entity_id}", json={"decision_data": data})
    assert preview.status_code == 200, preview.text
    body = preview.json()
    evidence = {"preview_token": body["preview_token"], "alternative_id": "reserve", "rationale": "I prefer current output to reserves because this allocation meets the immediate need while more spending can wait."}
    collection = "nations" if role == "president" else "companies"
    response = client.post(f"/api/sessions/{session_id}/{collection}/{entity_id}/decisions", json={"decision_data": {**data, "opportunity_cost": evidence}})
    assert response.status_code == 200, response.text


def test_seven_human_nations_and_drakmoor_finish_full_game(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db, session = closure_game()
    human_ids = [nation.id for nation in session.nations if nation.archetype != "Marginalized military state"]
    for year in range(1, 8):
        session.phase = PhaseEnum.PRESIDENTIAL
        for nation in session.nations:
            if nation.id in human_ids:
                submit_decision(db, session, "president", nation.id,
                    reviewed(db, session, "president", nation, {"government_spending": 100, "emergency_preparedness_investment": 25}))
        session.phase = PhaseEnum.COMPANY
        for nation in session.nations:
            if nation.id in human_ids:
                for company in nation.companies:
                    submit_decision(db, session, "company", company.id,
                        reviewed(db, session, "company", company, {"production_units": 1, "rnd_investment": 10}))
        session.phase = PhaseEnum.PROCESSING
        process_round(db, session)
    assert session.phase == PhaseEnum.COMPLETE
    assert db.query(DecisionReview).count() == 7 * (7 + 70)
    assert db.query(Decision).filter_by(submission_kind="automatic").count() == 7 * 11
    assert all(nation.treasury >= 0 for nation in session.nations)


def test_review_token_cannot_replay_into_another_round():
    db, session = closure_game()
    nation = session.nations[0]
    data = reviewed(db, session, "president", nation, {"government_spending": 100})
    session.current_round = 2
    db.add(Round(session_id=session.id, number=2)); db.commit()
    with pytest.raises(ValueError, match="refresh the comparison"):
        submit_decision(db, session, "president", nation.id, data)
