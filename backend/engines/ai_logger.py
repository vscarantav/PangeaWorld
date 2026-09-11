from sqlalchemy.orm import Session
from typing import Optional
try:
    from ..models.ai_chat import AIUsageLog
except ImportError:
    from models.ai_chat import AIUsageLog

def log_ai_usage(
    db: Session,
    user_id: int,
    session_id: int,
    round_number: int,
    phase: str,
    prompt_text: str,
    response_text: str,
    input_token_count: int,
    output_token_count: int,
    latency_ms: int,
    guardrail_flags: Optional[str] = None
) -> AIUsageLog:
    """Immutably record AI usage for instructor grading and analytics."""
    log = AIUsageLog(
        user_id=user_id,
        session_id=session_id,
        round_number=round_number,
        phase=phase,
        prompt_text=prompt_text,
        response_text=response_text,
        input_token_count=input_token_count,
        output_token_count=output_token_count,
        total_token_count=input_token_count + output_token_count,
        latency_ms=latency_ms,
        guardrail_flags=guardrail_flags
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
