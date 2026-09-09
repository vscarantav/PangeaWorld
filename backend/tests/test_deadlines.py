from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from auth import get_current_user
from database import get_db
from main import app
from models.domain import Decision, GameMembership, GameSession, Round, RoundStatus, User
from deadlines import utc_now
from tests.test_authorization import setup_game


def override_current_user_for_concurrency(role):
    db = next(app.dependency_overrides[get_db]())
    try:
        user = db.query(User).join(GameMembership).filter(GameMembership.role == role).first()
        db.expunge(user)
    finally:
        db.close()
    app.dependency_overrides[get_current_user] = lambda: user


def test_deadlines_reject_late_writes_record_autos_and_make_retries_idempotent():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}
    ).json()["phase"] == "presidential"
    session_view = instructor.get(f"/api/sessions/{game_id}").json()
    assert session_view["presidential_deadline_at"].endswith("+00:00")
    assert session_view["phase_duration_seconds"] == 172800

    pending = instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}
    )
    assert pending.status_code == 409

    db = next(app.dependency_overrides[get_db]())
    try:
        session = db.query(GameSession).filter_by(id=game_id).one()
        session.presidential_deadline_at = utc_now() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert president.post(
        f"/api/sessions/{game_id}/nations/{nation_id}/decisions", json={"decision_data": {}}
    ).status_code == 409
    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "presidential"}
    ).json()["phase"] == "company"
    seats = instructor.get(f"/api/sessions/{game_id}/readiness").json()["seats"]
    assert next(seat for seat in seats if seat["role"] == "president")["status"] == "auto_submitted"

    db = next(app.dependency_overrides[get_db]())
    try:
        session = db.query(GameSession).filter_by(id=game_id).one()
        session.company_deadline_at = utc_now() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert executive.put(
        f"/api/sessions/{game_id}/companies/{company_id}/draft", json={"decision_data": {}}
    ).status_code == 409
    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "company"}
    ).json()["phase"] == "processing"
    processed = instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "processing"}
    )
    assert processed.status_code == 200 and processed.json()["processed"] is True
    duplicate = instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "processing"}
    )
    assert duplicate.status_code == 200 and duplicate.json()["idempotent"] is True

    db = next(app.dependency_overrides[get_db]())
    try:
        decisions = db.query(Decision).join(Round).filter(Round.session_id == game_id).all()
        assert {(decision.player_type, decision.submission_kind, decision.auto_reason) for decision in decisions} == {
            ("president", "auto", "deadline_expired"),
            ("company", "auto", "deadline_expired"),
        }
        assert db.query(Round).filter_by(session_id=game_id, number=1, status=RoundStatus.COMPLETE).count() == 1
        assert db.query(Round).filter_by(session_id=game_id).count() == 2
    finally:
        db.close()
        app.dependency_overrides.clear()


def test_concurrent_phase_requests_only_transition_once():
    instructor, _, _, game_id, _, _ = setup_game()
    override_current_user_for_concurrency("instructor")
    parallel = TestClient(app)
    parallel.cookies.update(instructor.cookies)

    def advance(client):
        return client.post(
            f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}
        ).json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(advance, (instructor, parallel)))

    assert {response["phase"] for response in responses} == {"presidential"}
    assert sum(bool(response.get("idempotent")) for response in responses) == 1
    app.dependency_overrides.clear()


def test_simultaneous_duplicate_submissions_store_one_decision():
    instructor, president, _, game_id, nation_id, _ = setup_game()
    assert instructor.post(
        f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}
    ).status_code == 200
    override_current_user_for_concurrency("president")
    parallel = TestClient(app)
    parallel.cookies.update(president.cookies)

    def submit(client):
        return client.post(
            f"/api/sessions/{game_id}/nations/{nation_id}/decisions",
            json={"decision_data": {}},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, (president, parallel)))

    assert [response.status_code for response in responses] == [200, 200]
    db = next(app.dependency_overrides[get_db]())
    try:
        assert db.query(Decision).join(Round).filter(
            Round.session_id == game_id,
            Decision.player_type == "president",
            Decision.entity_id == nation_id,
        ).count() == 1
    finally:
        db.close()
        app.dependency_overrides.clear()


def test_session_websocket_broadcasts_identifier_only_phase_event():
    instructor, _, _, game_id, _, _ = setup_game()
    with instructor.websocket_connect(f"/api/sessions/{game_id}/ws") as websocket:
        assert websocket.receive_json() == {"type": "connected", "session_id": game_id}
        response = instructor.post(
            f"/api/sessions/{game_id}/advance", json={"expected_phase": "planning"}
        )
        assert response.status_code == 200
        event = websocket.receive_json()

    assert event == {
        "session_id": game_id,
        "type": "phase_changed",
        "round": 1,
        "phase": "presidential",
        "processed": False,
    }
    with instructor.websocket_connect(f"/api/sessions/{game_id}/ws") as reconnected:
        assert reconnected.receive_json() == {"type": "connected", "session_id": game_id}
    app.dependency_overrides.clear()
