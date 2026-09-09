from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.domain import AuthSession, GameMembership, User
from auth import SESSION_COOKIE


def make_client():
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
    return TestClient(app), db_session, engine


def teardown_function():
    app.dependency_overrides.clear()


def test_register_login_me_and_logout_never_expose_password_fields():
    client, db_session, _ = make_client()

    registered = client.post(
        "/api/auth/register",
        json={"email": "  Player@Example.com ", "password": "correct horse battery", "display_name": "Player One"},
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["user"]["email"] == "player@example.com"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]
    assert client.get("/api/auth/me").status_code == 200

    duplicate = client.post(
        "/api/auth/register",
        json={"email": "PLAYER@example.com", "password": "another password"},
    )
    assert duplicate.status_code == 409

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401

    second_client = TestClient(app)
    logged_in = second_client.post(
        "/api/auth/login",
        json={"email": "PLAYER@example.com", "password": "correct horse battery"},
    )
    assert logged_in.status_code == 200
    assert second_client.get("/api/auth/me").json()["user"]["display_name"] == "Player One"
    assert db_session().query(User).count() == 1


def test_invalid_credentials_and_expired_sessions_are_rejected():
    client, db_session, _ = make_client()
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": "missing@example.com", "password": "password"}).status_code == 401

    assert client.post("/api/auth/register", json={"email": "expiry@example.com", "password": "valid password"}).status_code == 201
    db = db_session()
    auth_session = db.query(AuthSession).one()
    auth_session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    db.close()
    assert client.get("/api/auth/me").status_code == 401


def test_login_revokes_the_previous_session_token():
    client, _, _ = make_client()
    assert client.post("/api/auth/register", json={"email": "rotation@example.com", "password": "valid password"}).status_code == 201
    old_token = client.cookies.get(SESSION_COOKIE)
    assert client.post("/api/auth/login", json={"email": "rotation@example.com", "password": "valid password"}).status_code == 200
    old_client = TestClient(app)
    old_client.cookies.set(SESSION_COOKIE, old_token)
    assert old_client.get("/api/auth/me").status_code == 401


def test_phase1_schema_and_new_auth_tables_are_created_together():
    _, _, engine = make_client()
    tables = set(inspect(engine).get_table_names())
    assert {"game_sessions", "nations", "companies", "rounds", "decisions"}.issubset(tables)
    assert {"users", "auth_sessions", "game_memberships"}.issubset(tables)
    membership_constraints = {item["name"] for item in inspect(engine).get_unique_constraints("game_memberships")}
    assert "uq_membership_seat_per_session" in membership_constraints

    db = sessionmaker(bind=engine)()
    user = User(email="member@example.com", password_hash="test-hash")
    db.add(user)
    db.commit()
    membership = GameMembership(session_id=999, user_id=user.id, role="instructor")
    # The membership model can be instantiated before a session is seeded;
    # foreign-key enforcement and assignment validation belong to Day 2.
    assert membership.role == "instructor"
    db.close()
