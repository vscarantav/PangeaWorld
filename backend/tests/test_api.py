from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


def test_session_and_decision_api_flow():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)

    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        map_snapshot = {
            "seed": "api-seed",
            "triangles": [{"id": 1, "terrain": "Ocean"}, {"id": 2, "terrain": "Plains"}],
            "edges": [{"id": 1, "triangle_ids": [1, 2], "is_impassable": True}],
            "countries": [{"id": str(index), "name": name} for index, name in enumerate(["Terranova", "Solhaven", "Korvath", "Valdoria", "Nordvik", "Zephyria", "Drakmoor", "Lunara"])],
            "cities": [{"id": index, "triangle_id": 2, "country_id": str(index // 8), "is_port": index in {32, 33, 48, 56, 57}} for index in range(64)],
        }
        created = client.post("/api/sessions", json={"seed": "api-seed", "map_snapshot": map_snapshot})
        assert created.status_code == 200
        session = created.json()
        session_id = session["id"]
        assert session["map_snapshot"]["seed"] == "api-seed"
        updated_map = client.put(f"/api/sessions/{session_id}/map", json={"map_snapshot": map_snapshot})
        assert updated_map.status_code == 200
        assert len(client.get(f"/api/sessions/{session_id}/nations").json()) == 8
        generated = client.post("/api/sessions", json={})
        assert generated.status_code == 200
        assert generated.json()["seed"]

        nation_id = client.get(f"/api/sessions/{session_id}/nations").json()[0]["id"]
        assert client.post(f"/api/sessions/{session_id}/advance").json()["phase"] == "presidential"
        assert client.post(f"/api/sessions/{session_id}/nations/{nation_id}/decisions",
                           json={"decision_data": {"government_spending": 25}}).status_code == 200
        assert client.post(f"/api/sessions/{session_id}/advance").json()["phase"] == "company"
        company_id = client.get(f"/api/sessions/{session_id}/companies").json()[0]["id"]
        assert client.post(f"/api/sessions/{session_id}/companies/{company_id}/decisions",
                           json={"decision_data": {"price": 150, "headcount": 20}}).status_code == 200
        assert client.post(f"/api/sessions/{session_id}/advance").json()["phase"] == "processing"
        processed = client.post(f"/api/sessions/{session_id}/advance")
        assert processed.status_code == 200
        assert processed.json()["processed"] is True
        refreshed = client.get(f"/api/sessions/{session_id}").json()
        assert refreshed["current_round"] == 2
        completed_round = next(round_ for round_ in refreshed["rounds"] if round_["number"] == 1)
        assert completed_round["results"]["nations"]
        assert client.get(f"/api/sessions/{session_id}/companies/{company_id}").json()["products"]["Widget"]["price"] == 150
        assert len(client.get(f"/api/sessions/{session_id}/news").json()["articles"]) >= 1
    finally:
        app.dependency_overrides.clear()
