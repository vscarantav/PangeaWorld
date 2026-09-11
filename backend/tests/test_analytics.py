from fastapi.testclient import TestClient

from main import app
from tests.test_authorization import setup_game


def test_instructor_analytics_are_read_only_and_exportable():
    instructor, president, executive, game_id, _nation_id, _company_id = setup_game()
    assert president.post(f"/api/sessions/{game_id}/advisor/chat", json={"prompt": "What trade-off does our budget create for capacity and risk?"}).status_code == 200

    guest = TestClient(app)
    assert guest.get(f"/api/sessions/{game_id}/analytics/engagement").status_code == 401
    assert president.get(f"/api/sessions/{game_id}/analytics/engagement").status_code == 403

    engagement = instructor.get(f"/api/sessions/{game_id}/analytics/engagement")
    assert engagement.status_code == 200
    player = next(item for item in engagement.json()["students"] if item["user_id"] != executive.get("/api/auth/me").json()["user"]["id"])
    assert player["ai_prompt_count"] == 1
    assert player["login_frequency"] is None

    grading = instructor.get(f"/api/sessions/{game_id}/analytics/ai-grading")
    assert grading.status_code == 200
    assert all("suggested_score" in item and item["instructor_override_required"] for item in grading.json()["grades"])
    assert instructor.get(f"/api/sessions/{game_id}/analytics/balance").status_code == 200
    assert instructor.get(f"/api/sessions/{game_id}/analytics/decisions").status_code == 200
    csv_export = instructor.get(f"/api/sessions/{game_id}/analytics/export?format=csv")
    assert csv_export.status_code == 200
    assert csv_export.headers["content-type"].startswith("text/csv")
    assert "section,user_id" in csv_export.text
