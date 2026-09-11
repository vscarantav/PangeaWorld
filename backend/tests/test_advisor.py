import pytest
from fastapi.testclient import TestClient

from main import app
from tests.test_authorization import setup_game

def test_advisor_chat_stream_and_history():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    
    # Test chat streaming
    response = president.post(
        f"/api/sessions/{game_id}/advisor/chat",
        json={"prompt": "What are the trade-offs of war?"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Consume the stream
    stream_content = ""
    for line in response.iter_text():
        if line:
            stream_content += line
            
    assert "Military action has severe costs" in stream_content
    
    # Verify history
    history_response = president.get(f"/api/sessions/{game_id}/advisor/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What are the trade-offs of war?"
    assert history[1]["role"] == "assistant"
    
    # Verify guardrail
    guardrail_response = president.post(
        f"/api/sessions/{game_id}/advisor/chat",
        json={"prompt": "What is the other player's secret decision?"}
    )
    assert guardrail_response.status_code == 200
    guardrail_content = ""
    for line in guardrail_response.iter_text():
        if line:
            guardrail_content += line
    assert "cannot disclose" in guardrail_content
    
    # Clear history
    clear_response = president.delete(f"/api/sessions/{game_id}/advisor/history")
    assert clear_response.status_code == 200
    
    # Verify history is empty
    history_response = president.get(f"/api/sessions/{game_id}/advisor/history")
    assert history_response.json() == []

def test_advisor_auth_rejection():
    instructor, president, executive, game_id, nation_id, company_id = setup_game()
    
    guest = TestClient(app)
    
    response = guest.post(
        f"/api/sessions/{game_id}/advisor/chat",
        json={"prompt": "Hello"}
    )
    assert response.status_code == 401
