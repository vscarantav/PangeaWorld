from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

try:
    from ..database import get_db
    from ..auth import get_current_user
    from ..models.domain import GameSession, GameMembership, User
    from ..models.ai_chat import AIConversation, AIMessage
    from ..engines.advisor import chat_stream, prompts_remaining
except ImportError:
    from database import get_db
    from auth import get_current_user
    from models.domain import GameSession, GameMembership, User
    from models.ai_chat import AIConversation, AIMessage
    from engines.advisor import chat_stream, prompts_remaining

router = APIRouter(prefix="/api/sessions/{session_id}/advisor", tags=["advisor"])

class ChatRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def chat_with_advisor(
    session_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    membership = db.query(GameMembership).filter(
        GameMembership.session_id == session_id,
        GameMembership.user_id == user.id
    ).first()
    
    if not membership or membership.role not in ["president", "executive"]:
        raise HTTPException(status_code=403, detail="Not authorized to use advisor in this session.")
        
    game_session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    remaining = prompts_remaining(db, user.id, session_id, game_session.phase.value)
    return StreamingResponse(
        chat_stream(
            db=db,
            user_id=user.id,
            session_id=session_id,
            role=membership.role,
            entity_id=membership.entity_id,
            prompt=request.prompt,
            round_number=game_session.current_round,
            phase=game_session.phase.value
        ),
        media_type="text/event-stream",
        headers={"X-Prompts-Remaining": str(remaining)}
    )

@router.get("/rate-limit")
def get_rate_limit(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    membership = db.query(GameMembership).filter(
        GameMembership.session_id == session_id,
        GameMembership.user_id == user.id
    ).first()
    if not membership or membership.role not in ["president", "executive"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    game_session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")
    remaining = prompts_remaining(db, user.id, session_id, game_session.phase.value)
    return {"remaining": remaining, "limit": 20}

@router.get("/history")
def get_chat_history(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    membership = db.query(GameMembership).filter(
        GameMembership.session_id == session_id,
        GameMembership.user_id == user.id
    ).first()
    
    if not membership or membership.role not in ["president", "executive"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
        
    conversation = db.query(AIConversation).filter(
        AIConversation.user_id == user.id,
        AIConversation.session_id == session_id,
        AIConversation.role == membership.role
    ).first()
    
    if not conversation:
        return []
        
    messages = db.query(AIMessage).filter(
        AIMessage.conversation_id == conversation.id
    ).order_by(AIMessage.timestamp.asc()).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "round": msg.round_number,
            "timestamp": msg.timestamp.isoformat()
        } for msg in messages
    ]

@router.delete("/history")
def clear_chat_history(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    membership = db.query(GameMembership).filter(
        GameMembership.session_id == session_id,
        GameMembership.user_id == user.id
    ).first()
    
    if not membership or membership.role not in ["president", "executive"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
        
    conversation = db.query(AIConversation).filter(
        AIConversation.user_id == user.id,
        AIConversation.session_id == session_id,
        AIConversation.role == membership.role
    ).first()
    
    if conversation:
        db.delete(conversation)
        db.commit()
        
    return {"status": "cleared"}
