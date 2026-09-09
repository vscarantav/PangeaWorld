from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


def persist_test_map(client, game):
    snapshot = {
        "seed": game["seed"],
        "triangles": [
            {"id": 1, "terrain": "Ocean", "points": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 1}]},
            {"id": 2, "terrain": "Solhaven", "points": [{"x": 1, "y": 0}, {"x": 1, "y": 1}, {"x": 0, "y": 1}]},
        ],
        "edges": [{"id": "0.0,0.0-1.0,0.0", "p1": {"x": 0, "y": 0}, "p2": {"x": 1, "y": 0}, "triangle_ids": [1, 2], "is_impassable": True}],
        "countries": [{"id": str(index), "name": name, "x": index * 7, "y": 0} for index, name in enumerate(["Terranova", "Solhaven", "Korvath", "Valdoria", "Nordvik", "Zephyria", "Drakmoor", "Lunara"])],
        "cities": [{"id": index, "triangle_id": 2, "country_id": str(index // 8), "is_port": index in {32, 33, 48, 56, 57}} for index in range(64)],
    }
    assert client.put(f"/api/sessions/{game['id']}/map", json={"map_snapshot": snapshot}).status_code == 200


def make_client():
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
    return TestClient(app)


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": "a safe password"})
    assert response.status_code == 201
    return response.json()["user"]


def test_instructor_assigns_lobby_members_to_session_local_seats():
    instructor = make_client()
    register(instructor, "teacher@example.com")
    game = instructor.post("/api/sessions", json={}).json()
    lobby = instructor.get(f"/api/sessions/{game['id']}/lobby").json()
    assert lobby["my_membership"]["role"] == "instructor"
    assert lobby["join_code"]

    president = TestClient(app)
    player = register(president, "president@example.com")
    joined = president.post("/api/sessions/lobby/join", json={"join_code": lobby["join_code"]})
    assert joined.status_code == 200
    nation = lobby["seats"]["nations"][0]
    assignment = instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": player["id"], "role": "president", "entity_id": nation["id"]})
    assert assignment.status_code == 200
    assert assignment.json()["membership"]["entity_id"] == nation["id"]

    duplicate = TestClient(app); other = register(duplicate, "other@example.com")
    duplicate.post("/api/sessions/lobby/join", json={"join_code": lobby["join_code"]})
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": other["id"], "role": "president", "entity_id": nation["id"]}).status_code == 409

    foreign_game = instructor.post("/api/sessions", json={}).json()
    foreign_lobby = instructor.get(f"/api/sessions/{foreign_game['id']}/lobby").json()
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": other["id"], "role": "executive", "entity_id": foreign_lobby["seats"]["companies"][0]["id"]}).status_code == 422
    app.dependency_overrides.clear()


def test_join_code_is_revoked_when_game_starts():
    instructor = make_client(); register(instructor, "teacher2@example.com")
    game = instructor.post("/api/sessions", json={}).json()
    persist_test_map(instructor, game)
    code = instructor.get(f"/api/sessions/{game['id']}/lobby").json()["join_code"]
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/start").status_code == 200
    newcomer = TestClient(app); register(newcomer, "new@example.com")
    assert newcomer.post("/api/sessions/lobby/join", json={"join_code": code}).status_code == 404
    app.dependency_overrides.clear()


def test_game_cannot_start_until_a_validated_map_is_persisted():
    instructor = make_client(); register(instructor, "map-teacher@example.com")
    game = instructor.post("/api/sessions", json={}).json()
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/start").status_code == 409
    persist_test_map(instructor, game)
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/start").status_code == 200


def test_four_accounts_receive_two_presidential_and_two_executive_seats_then_start():
    instructor = make_client(); register(instructor, "four-teacher@example.com")
    game = instructor.post("/api/sessions", json={}).json()
    persist_test_map(instructor, game)
    lobby = instructor.get(f"/api/sessions/{game['id']}/lobby").json()
    players = []
    for number in range(4):
        client = TestClient(app)
        user = register(client, f"player{number}@example.com")
        assert client.post("/api/sessions/lobby/join", json={"join_code": lobby["join_code"]}).status_code == 200
        players.append((client, user))
    first_nation, second_nation = lobby["seats"]["nations"][:2]
    seats = [("president", first_nation["id"]), ("president", second_nation["id"]),
             ("executive", next(company["id"] for company in lobby["seats"]["companies"] if company["nation_id"] == first_nation["id"])),
             ("executive", next(company["id"] for company in lobby["seats"]["companies"] if company["nation_id"] == second_nation["id"]))]
    for (_, user), (role, entity_id) in zip(players, seats):
        assert instructor.post(f"/api/sessions/{game['id']}/lobby/assign", json={"user_id": user["id"], "role": role, "entity_id": entity_id}).status_code == 200
    assert instructor.post(f"/api/sessions/{game['id']}/lobby/start").status_code == 200
    for (client, _), (role, entity_id) in zip(players, seats):
        mine = client.get(f"/api/sessions/{game['id']}/lobby").json()["my_membership"]
        assert (mine["role"], mine["entity_id"]) == (role, entity_id)
    app.dependency_overrides.clear()


def test_round_one_rename_is_unique_authorized_and_audited():
    instructor = make_client(); register(instructor, "rename-teacher@example.com")
    game = instructor.post("/api/sessions", json={}).json()
    persist_test_map(instructor, game)
    lobby = instructor.get(f"/api/sessions/{game['id']}/lobby").json()
    nation_id = lobby["seats"]["nations"][0]["id"]
    assert instructor.put(f"/api/sessions/{game['id']}/nations/{nation_id}/name", json={"name": "New Terranova"}).json()["name"] == "New Terranova"
    snapshot = instructor.get(f"/api/sessions/{game['id']}").json()["map_snapshot"]
    assert any(country["name"] == "New Terranova" for country in snapshot["countries"])
    assert instructor.put(f"/api/sessions/{game['id']}/nations/{lobby['seats']['nations'][1]['id']}/name", json={"name": "New Terranova"}).status_code == 409
    assert instructor.put(f"/api/sessions/{game['id']}/nations/{nation_id}/name", json={"name": "admin"}).status_code == 422
    assert instructor.put(f"/api/sessions/{game['id']}/nations/{nation_id}/name", json={"name": "F.u.c.k"}).status_code == 422
    assert instructor.put(f"/api/sessions/{game['id']}/nations/{nation_id}/name", json={"name": "Shitland"}).status_code == 422
    db = next(app.dependency_overrides[get_db]())
    try:
        from models.domain import LobbyAudit
        assert db.query(LobbyAudit).filter_by(session_id=game["id"], action="rename").count() == 1
    finally:
        db.close()
    app.dependency_overrides.clear()
