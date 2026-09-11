from fastapi.testclient import TestClient

from database import get_db
from main import app
from models.domain import DecisionReview, GameSession, PhaseEnum, Round
from tests.test_authorization import setup_game


def test_backfill_status_and_instructor_takeover():
    instructor, president, _executive, game_id, nation_id, _company_id = setup_game()
    waiting = TestClient(app)
    user = waiting.post("/api/auth/register", json={"email": "waiting@backfill.test", "password": "a safe password"}).json()["user"]
    lobby = instructor.get(f"/api/sessions/{game_id}/lobby").json()
    # Closed lobbies cannot accept new users, so make an existing unassigned membership directly for this integration fixture.
    db = next(app.dependency_overrides[get_db]())
    try:
        from models.domain import GameMembership
        db.add(GameMembership(session_id=game_id, user_id=user["id"], role="player")); db.commit()
    finally: db.close()
    assert president.get(f"/api/sessions/{game_id}/backfill/status").status_code == 403
    body = instructor.get(f"/api/sessions/{game_id}/backfill/status").json()
    vacant = next(item for item in body["seats"] if item["control"] == "ai" and item["role"] == "president")
    takeover = instructor.post(f"/api/sessions/{game_id}/backfill/{vacant['seat_id']}/takeover", json={"user_id": user["id"]})
    assert takeover.status_code == 200
    assert takeover.json()["control"] == "human"
    assert instructor.post(f"/api/sessions/{game_id}/backfill/president:{nation_id}/takeover", json={"user_id": user["id"]}).status_code == 409
    app.dependency_overrides.clear()


def test_debrief_is_post_game_and_uses_recorded_alternative_only():
    instructor, president, _executive, game_id, nation_id, _company_id = setup_game()
    assert president.get(f"/api/sessions/{game_id}/debrief/timeline").status_code == 409
    db = next(app.dependency_overrides[get_db]())
    try:
        game = db.get(GameSession, game_id); game.phase = PhaseEnum.COMPLETE
        round_ = db.query(Round).filter_by(session_id=game_id, number=1).one()
        review = DecisionReview(round_id=round_.id, player_type="president", entity_id=nation_id, record={
            "selected": {"government_spending": 10}, "assumptions": {"remaining": 90, "committed": 10},
            "foregone": {"id": "reserve", "label": "Keep reserves", "remaining": 100, "commitment": 0, "projection": {"liquidity": 100}},
        })
        db.add(review); db.commit(); db.refresh(review); review_id = review.id
    finally: db.close()
    timeline = president.get(f"/api/sessions/{game_id}/debrief/timeline")
    assert timeline.status_code == 200 and timeline.json()["timeline"][0]["round"] == 1
    what_if = president.post(f"/api/sessions/{game_id}/debrief/what-if", json={"decision_review_id": review_id})
    assert what_if.status_code == 200
    assert what_if.json()["estimate"] is True
    assert "not a guaranteed outcome" in what_if.json()["label"]
    assert president.get(f"/api/sessions/{game_id}/debrief/connections").status_code == 200
    app.dependency_overrides.clear()
