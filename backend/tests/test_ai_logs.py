from fastapi.testclient import TestClient

from main import app
from tests.test_authorization import setup_game
from models.ai_chat import AIUsageLog

def test_ai_usage_logging_endpoints():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    
    # 1. Generate some logs (e.g. from a mock chat)
    response = president.post(
        f"/api/sessions/{game_id}/advisor/chat",
        json={"prompt": "President test prompt"}
    )
    assert response.status_code == 200
    for _ in response.iter_text():
        pass
        
    response2 = executive.post(
        f"/api/sessions/{game_id}/advisor/chat",
        json={"prompt": "Executive test prompt"}
    )
    assert response2.status_code == 200
    for _ in response2.iter_text():
        pass
        
    # 2. Test Instructor authorization
    guest = TestClient(app)
    assert guest.get(f"/api/sessions/{game_id}/ai-usage").status_code == 401
    assert president.get(f"/api/sessions/{game_id}/ai-usage").status_code == 403
    
    # 3. Test Instructor getting stats
    stats_response = instructor.get(f"/api/sessions/{game_id}/ai-usage")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert len(stats) == 2
    for stat in stats:
        assert stat["message_count"] == 1
        assert stat["total_tokens"] > 0
        
    # 4. Test Instructor getting detailed logs for a user
    target_user_id = stats[0]["user_id"]
    detail_response = instructor.get(f"/api/sessions/{game_id}/ai-usage/{target_user_id}")
    assert detail_response.status_code == 200
    details = detail_response.json()
    assert len(details) == 1
    assert "prompt" in details[0]
    assert "response" in details[0]
    assert "tokens" in details[0]
