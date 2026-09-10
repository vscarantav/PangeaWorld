from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from deadlines import utc_now
from main import app
from models.domain import Decision, GameSession, Round, RoundStatus
from tests.test_lobby import persist_test_map


PASSWORD = "four-player-password"


def setup_four_player_game():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def override():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    instructor = TestClient(app)
    assert instructor.post(
        "/api/auth/register", json={"email": "teacher@four.test", "password": PASSWORD}
    ).status_code == 201
    game = instructor.post("/api/sessions", json={"phase_duration_seconds": 5}).json()
    persist_test_map(instructor, game)
    lobby = instructor.get(f"/api/sessions/{game['id']}/lobby").json()
    nations = lobby["seats"]["nations"][:2]
    companies = [
        next(company for company in lobby["seats"]["companies"] if company["nation_id"] == nation["id"])
        for nation in nations
    ]
    assignments = [
        ("president", nations[0]["id"]),
        ("president", nations[1]["id"]),
        ("executive", companies[0]["id"]),
        ("executive", companies[1]["id"]),
    ]
    players = []
    for index, (role, entity_id) in enumerate(assignments):
        client = TestClient(app)
        email = f"player{index}@four.test"
        user = client.post("/api/auth/register", json={"email": email, "password": PASSWORD}).json()["user"]
        assert client.post("/api/sessions/lobby/join", json={"join_code": lobby["join_code"]}).status_code == 200
        assert instructor.post(
            f"/api/sessions/{game['id']}/lobby/assign",
            json={"user_id": user["id"], "role": role, "entity_id": entity_id},
        ).status_code == 200
        players.append({"client": client, "email": email, "role": role, "entity_id": entity_id})

    assert instructor.post(f"/api/sessions/{game['id']}/lobby/start").status_code == 200
    return instructor, players, game, nations


def test_four_players_complete_one_authoritative_round_with_one_deadline_auto():
    instructor, players, game, nations = setup_four_player_game()
    game_id = game["id"]
    original_map = instructor.get(f"/api/sessions/{game_id}").json()["map_snapshot"]

    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}
    ).json()["phase"] == "presidential"
    for executive in players[2:]:
        assert executive["client"].post(
            f"/api/sessions/{game_id}/companies/{executive['entity_id']}/decisions",
            json={"decision_data": {}},
        ).status_code == 409
    for index, president in enumerate(players[:2]):
        assert president["client"].post(
            f"/api/sessions/{game_id}/nations/{president['entity_id']}/decisions",
            json={"decision_data": {"government_spending": 20 + index, "tax_rate": 0.2 + index / 100}},
        ).status_code == 200

    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}
    ).json()["phase"] == "company"
    submitting_executive, missing_executive = players[2:]
    supplier_id = next(
        nation["id"] for nation in instructor.get(f"/api/sessions/{game_id}/nations").json()
        if nation["name"] == "Valdoria"
    )
    submission = submitting_executive["client"].post(
        f"/api/sessions/{game_id}/companies/{submitting_executive['entity_id']}/decisions",
        json={"decision_data": {
            "price": 175,
            "headcount": 25,
            "production_units": 1.2,
            "rnd_investment": 100,
            "sourcing": [{"resource_type": "Energy", "supplier_nation_id": supplier_id,
                          "quantity": 1, "mode": "rail"}],
        }},
    )
    assert submission.status_code == 200, submission.text
    assert missing_executive["client"].put(
        f"/api/sessions/{game_id}/companies/{missing_executive['entity_id']}/draft",
        json={"decision_data": {"price": 180}},
    ).status_code == 200

    db = next(app.dependency_overrides[get_db]())
    try:
        session = db.query(GameSession).filter_by(id=game_id).one()
        session.company_deadline_at = utc_now() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "company"}
    ).json()["phase"] == "processing"
    processed = instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "processing"}
    )
    assert processed.status_code == 200 and processed.json()["processed"] is True
    duplicate = instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "processing"}
    ).json()
    assert duplicate["idempotent"] is True and duplicate["round"] == 2

    session_views = [player["client"].get(f"/api/sessions/{game_id}").json() for player in players]
    round_results = [next(round_ for round_ in view["rounds"] if round_["number"] == 1)["results"]
                     for view in session_views]
    assert all(view["current_round"] == 2 and view["phase"] == "planning" for view in session_views)
    assert all(result == round_results[0] for result in round_results[1:])
    news = [player["client"].get(f"/api/sessions/{game_id}/news").json() for player in players]
    assert news[0]["articles"] and all(feed == news[0] for feed in news[1:])

    db = next(app.dependency_overrides[get_db]())
    try:
        decisions = db.query(Decision).join(Round).filter(Round.session_id == game_id).all()
        automatic = next(decision for decision in decisions if decision.submission_kind == "auto")
        assert automatic.entity_id == missing_executive["entity_id"]
        assert automatic.auto_reason == "deadline_expired" and automatic.submitted_at is not None
        assert len(decisions) == 4
        assert db.query(Round).filter_by(
            session_id=game_id, number=1, status=RoundStatus.COMPLETE
        ).count() == 1
    finally:
        db.close()

    restored = players[0]
    assert restored["client"].post("/api/auth/logout").status_code == 200
    assert restored["client"].post(
        "/api/auth/login", json={"email": restored["email"], "password": PASSWORD}
    ).status_code == 200
    restored_lobby = restored["client"].get(f"/api/sessions/{game_id}/lobby").json()
    restored_session = restored["client"].get(f"/api/sessions/{game_id}").json()
    assert restored_lobby["my_membership"]["role"] == "president"
    assert restored_lobby["my_membership"]["entity_id"] == nations[0]["id"]
    assert restored_session["phase"] == "planning" and restored_session["current_round"] == 2
    assert restored_session["map_snapshot"] == original_map
    app.dependency_overrides.clear()
