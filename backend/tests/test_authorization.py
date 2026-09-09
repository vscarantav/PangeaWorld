from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from tests.test_lobby import persist_test_map
from models.domain import GameMembership, GameSession, PhaseEnum, User


def setup_game():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine); factory = sessionmaker(bind=engine)
    def override():
        db = factory()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override
    instructor = TestClient(app)
    assert instructor.post("/api/auth/register", json={"email": "instructor@auth.test", "password": "a safe password"}).status_code == 201
    game = instructor.post("/api/sessions", json={}).json(); lobby = instructor.get(f"/api/sessions/{game['id']}/lobby").json()
    persist_test_map(instructor, game)
    players = []
    for number in range(2):
        client = TestClient(app)
        user = client.post("/api/auth/register", json={"email": f"player{number}@auth.test", "password": "a safe password"}).json()["user"]
        client.post("/api/sessions/lobby/join", json={"join_code": lobby["join_code"]})
        players.append((client, user))
    nation_id = lobby["seats"]["nations"][0]["id"]; company_id = lobby["seats"]["companies"][0]["id"]
    instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": players[0][1]["id"], "role": "president", "entity_id": nation_id})
    instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": players[1][1]["id"], "role": "executive", "entity_id": company_id})
    instructor.post(f"/api/sessions/{game['id']}/lobby/start")
    return instructor, players[0][0], players[1][0], game["id"], nation_id, company_id


def test_protected_routes_reject_guests_and_cross_seat_actions():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    guest = TestClient(app)
    assert guest.get(f"/api/sessions/{game_id}").status_code == 401
    assert guest.get(f"/api/sessions/{game_id}/market").status_code == 401
    assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}).status_code == 200
    assert executive.post(f"/api/sessions/{game_id}/nations/{nation_id}/decisions", json={"decision_data": {}}).status_code == 403
    assert president.post(f"/api/sessions/{game_id}/nations/{nation_id}/decisions", json={"decision_data": {}}).status_code == 200
    assert president.post(f"/api/sessions/{game_id}/companies/{company_id}/decisions", json={"decision_data": {}}).status_code == 403
    assert president.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}).status_code == 403
    assert instructor.get(f"/api/sessions/{game_id}/readiness").json()["submitted"] == 1
    private_readiness = president.get(f"/api/sessions/{game_id}/readiness")
    assert private_readiness.status_code == 200
    private_body = private_readiness.json()
    assert {key: private_body[key] for key in ("round", "phase", "my_status")} == {
        "round": 1, "phase": "presidential", "my_status": "submitted"
    }
    assert private_body["deadline_at"] and private_body["server_time"]
    assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}).status_code == 200
    assert president.post(f"/api/sessions/{game_id}/nations/{nation_id}/decisions", json={"decision_data": {}}).status_code == 409
    app.dependency_overrides.clear()


def test_company_detail_is_private_and_map_is_instructor_lobby_only():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    assert president.get(f"/api/sessions/{game_id}/companies/{company_id}").status_code == 200
    assert executive.get(f"/api/sessions/{game_id}/companies/{company_id}").status_code == 200
    own_nation = executive.get(f"/api/sessions/{game_id}/nations/{nation_id}")
    assert own_nation.status_code == 200
    assert "companies" not in own_nation.json()
    other_company_id = next(item["id"] for item in instructor.get(f"/api/sessions/{game_id}/companies").json() if item["id"] != company_id)
    assert executive.get(f"/api/sessions/{game_id}/companies/{other_company_id}").status_code == 403
    assert executive.put(f"/api/sessions/{game_id}/map", json={"map_snapshot": {}}).status_code == 403
    assert instructor.put(f"/api/sessions/{game_id}/map", json={"map_snapshot": {}}).status_code == 409
    app.dependency_overrides.clear()


def test_unassigned_members_cannot_read_game_data_and_players_cannot_create_games():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    unassigned = TestClient(app)
    assert unassigned.post("/api/auth/register", json={"email": "unassigned@auth.test", "password": "a safe password"}).status_code == 201
    db = next(app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter_by(email="unassigned@auth.test").one()
        db.add(GameMembership(session_id=game_id, user_id=user.id, role="player")); db.commit()
    finally:
        db.close()
    assert unassigned.get(f"/api/sessions/{game_id}/nations").status_code == 403
    assert president.post("/api/sessions", json={}).status_code == 403
    app.dependency_overrides.clear()


def test_server_drafts_are_private_and_visible_to_readiness_without_payloads():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    assert instructor.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}).status_code == 200
    draft = president.put(f"/api/sessions/{game_id}/nations/{nation_id}/draft", json={"decision_data": {"government_spending": 1}})
    assert draft.status_code == 200
    assert instructor.get(f"/api/sessions/{game_id}/readiness").json()["seats"][0]["status"] == "draft"
    assert "decision_data" not in instructor.get(f"/api/sessions/{game_id}/readiness").text
    app.dependency_overrides.clear()


def test_legacy_session_can_be_claimed_by_an_instructor():
    instructor, _, _, _, _, _ = setup_game()
    db = next(app.dependency_overrides[get_db]())
    try:
        legacy = GameSession(seed="legacy-seed", phase=PhaseEnum.PLANNING, status="active")
        db.add(legacy); db.commit(); db.refresh(legacy)
        legacy_id = legacy.id
    finally:
        db.close()
    recoverable = instructor.get("/api/sessions/legacy/recoverable")
    assert recoverable.status_code == 200
    assert any(item["id"] == legacy_id and not item["has_map_snapshot"] for item in recoverable.json())
    claimed = instructor.post(f"/api/sessions/{legacy_id}/claim-legacy")
    assert claimed.status_code == 200
    assert claimed.json()["requires_map_rebuild"] is True
    assert claimed.json()["session"]["status"] == "lobby"
    recovered_lobby = instructor.get(f"/api/sessions/{legacy_id}/lobby").json()
    assert len(recovered_lobby["seats"]["nations"]) == 8
    assert len(recovered_lobby["seats"]["companies"]) == 80
    persist_test_map(instructor, claimed.json()["session"])
    assert instructor.post(f"/api/sessions/{legacy_id}/lobby/start").status_code == 200
    assert instructor.get(f"/api/sessions/{legacy_id}").status_code == 200
    app.dependency_overrides.clear()


def test_cross_session_reads_and_commands_are_rejected():
    instructor, president, executive, game_id, _, _ = setup_game()
    other_game = instructor.post("/api/sessions", json={}).json()
    persist_test_map(instructor, other_game)
    other_lobby = instructor.get(f"/api/sessions/{other_game['id']}/lobby").json()
    other_nation_id = other_lobby["seats"]["nations"][0]["id"]
    other_company_id = other_lobby["seats"]["companies"][0]["id"]

    assert president.get(f"/api/sessions/{other_game['id']}").status_code == 403
    assert president.get("/api/sessions/legacy/recoverable").status_code == 403
    assert president.get(f"/api/sessions/{other_game['id']}/nations/{other_nation_id}").status_code == 403
    assert executive.get(f"/api/sessions/{other_game['id']}/companies/{other_company_id}").status_code == 403
    assert executive.post(f"/api/sessions/{other_game['id']}/companies/{other_company_id}/decisions", json={"decision_data": {}}).status_code == 403
    assert president.post(f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}).status_code == 403
    app.dependency_overrides.clear()
