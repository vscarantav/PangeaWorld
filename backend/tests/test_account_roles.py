from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


PASSWORD = "a secure classroom password"


def make_environment():
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


def teardown_function():
    app.dependency_overrides.clear()


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201
    return response.json()["user"]


def login(email):
    client = TestClient(app)
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return client


def test_bootstrap_admin_and_role_boundaries_are_enforced():
    admin = make_environment()
    first = register(admin, "admin@roles.test")
    assert first["account_type"] == "admin"
    assert first["is_instructor"] is True

    student = TestClient(app)
    second = register(student, "student@roles.test")
    assert second["account_type"] == "student"
    assert student.post("/api/sessions", json={}).status_code == 403
    assert student.post("/api/accounts/users", json={
        "email": "forbidden@roles.test", "password": PASSWORD, "account_type": "student",
    }).status_code == 403

    professor_result = admin.post("/api/accounts/users", json={
        "email": "professor@roles.test", "password": PASSWORD,
        "display_name": "Professor Rivera", "account_type": "professor",
    })
    assert professor_result.status_code == 201
    assert professor_result.json()["user"]["account_type"] == "professor"

    professor = login("professor@roles.test")
    created_student = professor.post("/api/accounts/users", json={
        "email": "managed@roles.test", "password": PASSWORD,
        "display_name": "Managed Student", "account_type": "student",
    })
    assert created_student.status_code == 201
    assert professor.post("/api/accounts/users", json={
        "email": "other-professor@roles.test", "password": PASSWORD, "account_type": "professor",
    }).status_code == 403

    professor_dashboard = professor.get("/api/accounts/dashboard").json()
    assert [item["email"] for item in professor_dashboard["users"]] == ["managed@roles.test"]
    admin_dashboard = admin.get("/api/accounts/dashboard").json()
    assert admin_dashboard["counts"] == {"admin": 1, "professor": 1, "student": 2}


def test_professor_can_play_and_still_manage_while_admin_can_enter_any_session():
    admin = make_environment()
    register(admin, "admin-session@roles.test")
    admin.post("/api/accounts/users", json={
        "email": "playing-professor@roles.test", "password": PASSWORD,
        "display_name": "Playing Professor", "account_type": "professor",
    })
    professor = login("playing-professor@roles.test")

    game_response = professor.post("/api/sessions", json={"owner_role": "president"})
    assert game_response.status_code == 200
    game = game_response.json()
    lobby = professor.get(f"/api/sessions/{game['id']}/lobby").json()
    assert lobby["can_manage"] is True
    assert lobby["my_membership"]["role"] == "president"
    assert lobby["my_membership"]["entity_id"] is not None

    admin_dashboard = admin.get("/api/accounts/dashboard").json()
    tracked = next(item for item in admin_dashboard["sessions"] if item["id"] == game["id"])
    assert tracked["owner_name"] == "Playing Professor"
    assert tracked["assigned_seats"] == 1
    assert tracked["is_member"] is False

    access = admin.post(f"/api/accounts/sessions/{game['id']}/access")
    assert access.status_code == 200
    admin_lobby = admin.get(f"/api/sessions/{game['id']}/lobby").json()
    assert admin_lobby["can_manage"] is True
    assert admin_lobby["my_membership"]["role"] == "instructor"
