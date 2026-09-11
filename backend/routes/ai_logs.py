from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from ..database import get_db
    from ..auth import get_current_user
    from ..models.domain import User
    from ..models.ai_chat import AIUsageLog
except ImportError:
    from database import get_db
    from auth import get_current_user
    from models.domain import User
    from models.ai_chat import AIUsageLog

router = APIRouter(prefix="/api/sessions/{session_id}/ai-usage", tags=["ai_usage"])

@router.get("")
def get_ai_usage_stats(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="Instructor access required")
        
    stats = db.query(
        AIUsageLog.user_id,
        func.count(AIUsageLog.id).label("message_count"),
        func.sum(AIUsageLog.total_token_count).label("total_tokens")
    ).filter(AIUsageLog.session_id == session_id).group_by(AIUsageLog.user_id).all()
    
    return [
        {
            "user_id": stat.user_id,
            "message_count": stat.message_count,
            "total_tokens": stat.total_tokens or 0
        } for stat in stats
    ]

@router.get("/{target_user_id}")
def get_user_ai_usage(
    session_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="Instructor access required")
        
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.session_id == session_id,
        AIUsageLog.user_id == target_user_id
    ).order_by(AIUsageLog.timestamp.asc()).all()
    
    return [
        {
            "id": log.id,
            "round_number": log.round_number,
            "phase": log.phase,
            "prompt": log.prompt_text,
            "response": log.response_text,
            "tokens": log.total_token_count,
            "latency_ms": log.latency_ms,
            "guardrail_flags": log.guardrail_flags,
            "timestamp": log.timestamp.isoformat()
        } for log in logs
    ]
