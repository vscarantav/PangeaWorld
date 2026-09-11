import json
import asyncio
from typing import AsyncGenerator
from sqlalchemy.orm import Session

try:
    from ..models.domain import Nation, Company, GameSession
    from ..models.ai_chat import AIConversation, AIMessage, AIMessageRole
    from ..engines.ai_logger import log_ai_usage
except ImportError:
    from models.domain import Nation, Company, GameSession
    from models.ai_chat import AIConversation, AIMessage, AIMessageRole
    from engines.ai_logger import log_ai_usage

COMPANY_SYSTEM_PROMPT = """You are a strategic advisor to a Company Executive in PangeaWorld.
Use the Socratic method. Guide the executive to think critically about their supply chain, pricing, margins, and market share.
Do not give direct answers or optimal solutions.
Consider the executive's financials and constraints.
"""

PRESIDENT_SYSTEM_PROMPT = """You are a strategic advisor to a National President in PangeaWorld.
Use the Socratic method. Guide the president to think critically about macroeconomics, geopolitics, military strategy, and fiscal policy.
Do not give direct answers or optimal solutions.
Consider the president's treasury, approval rating, and military readiness.
"""

def _build_context(db: Session, session_id: int, role: str, entity_id: int) -> str:
    # Gather relevant contextual information for the prompt
    game_session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not game_session:
        return ""
        
    context = f"Current Round: {game_session.current_round}, Phase: {game_session.phase.value}\n"
    
    if role == "president":
        nation = db.query(Nation).filter(Nation.id == entity_id).first()
        if nation:
            context += f"Nation: {nation.name}\n"
            context += f"GDP: {nation.gdp}, CPI: {nation.cpi}, Treasury: {nation.treasury}\n"
            context += f"Approval: {nation.approval_rating}, Military Readiness: {nation.military_readiness}\n"
    elif role == "executive":
        company = db.query(Company).filter(Company.id == entity_id).first()
        if company:
            context += f"Company: {company.name}\n"
            context += f"Cash: {company.cash}, Revenue: {company.revenue}, Profit: {company.net_profit}\n"
            
    return context

async def generate_mock_stream(prompt: str, context: str, system_prompt: str) -> AsyncGenerator[str, None]:
    """Mock the Gemini provider stream using Socratic responses based on keywords."""
    prompt_lower = prompt.lower()
    
    response_words = []
    if "tariff" in prompt_lower or "tax" in prompt_lower:
        response_words = "What impact do you think raising tariffs will have on your domestic consumers and international trade partners? Consider both the short-term revenue and the long-term diplomatic consequences.".split(" ")
    elif "r&d" in prompt_lower or "research" in prompt_lower or "marketing" in prompt_lower:
        response_words = "Investing in R&D or marketing consumes capital today. What alternative uses of that capital are you giving up, and what is your expected timeframe for a return on this investment?".split(" ")
    elif "war" in prompt_lower or "attack" in prompt_lower or "military" in prompt_lower:
        response_words = "Military action has severe costs, both financial and political. How will this affect your approval rating and civilian infrastructure projects? Is there a diplomatic alternative you haven't considered?".split(" ")
    else:
        response_words = "That is an interesting perspective. What are the key trade-offs involved in that decision, and what is your next-best alternative?".split(" ")
        
    for word in response_words:
        yield f"{word} "
        await asyncio.sleep(0.01)


RATE_LIMIT_PER_PHASE = 20  # configurable default

def get_usage_count(db: Session, user_id: int, session_id: int, phase: str) -> int:
    """Return how many prompts this user has sent in the current phase."""
    try:
        from ..models.ai_chat import AIUsageLog
    except ImportError:
        from models.ai_chat import AIUsageLog
    return db.query(AIUsageLog).filter(
        AIUsageLog.user_id == user_id,
        AIUsageLog.session_id == session_id,
        AIUsageLog.phase == phase
    ).count()


def prompts_remaining(db: Session, user_id: int, session_id: int, phase: str) -> int:
    used = get_usage_count(db, user_id, session_id, phase)
    return max(0, RATE_LIMIT_PER_PHASE - used)

async def chat_stream(
    db: Session,
    user_id: int,
    session_id: int,
    role: str,
    entity_id: int,
    prompt: str,
    round_number: int,
    phase: str
) -> AsyncGenerator[str, None]:
    import time
    start_ms = int(time.monotonic() * 1000)

    # 0. Rate limit check
    remaining = prompts_remaining(db, user_id, session_id, phase)
    if remaining <= 0:
        yield f"You have reached the prompt limit ({RATE_LIMIT_PER_PHASE}) for this phase. Your prompts will reset next phase."
        return

    # 1. Guardrail checks (simple mock implementation)
    guardrail_triggered = (
        "other player" in prompt.lower() or "secret" in prompt.lower()
    )
    if guardrail_triggered:
        rejection = "I cannot disclose other players' private data or secret decisions."
        yield rejection
        # Log the blocked interaction so instructors can see guardrail activations
        log_ai_usage(
            db=db,
            user_id=user_id,
            session_id=session_id,
            round_number=round_number,
            phase=phase,
            prompt_text=prompt,
            response_text=rejection,
            input_token_count=len(prompt.split()),
            output_token_count=len(rejection.split()),
            latency_ms=int(time.monotonic() * 1000) - start_ms,
            guardrail_flags="cross_player_data_request"
        )
        return
        
    # 2. Retrieve or create conversation
    conversation = db.query(AIConversation).filter(
        AIConversation.user_id == user_id,
        AIConversation.session_id == session_id,
        AIConversation.role == role
    ).first()
    
    if not conversation:
        conversation = AIConversation(user_id=user_id, session_id=session_id, role=role)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
    # 3. Build context
    context = _build_context(db, session_id, role, entity_id)
    system_prompt = PRESIDENT_SYSTEM_PROMPT if role == "president" else COMPANY_SYSTEM_PROMPT
    
    # 4. Save user message
    user_msg = AIMessage(
        conversation_id=conversation.id,
        role=AIMessageRole.USER,
        content=prompt,
        token_count=len(prompt.split()), # Mock token count
        round_number=round_number,
        phase=phase
    )
    db.add(user_msg)
    conversation.message_count += 1
    db.commit()
    
    # 5. Stream response and collect it
    full_response = ""
    async for chunk in generate_mock_stream(prompt, context, system_prompt):
        full_response += chunk
        yield chunk
        
    # 6. Save assistant message and usage log
    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        role=AIMessageRole.ASSISTANT,
        content=full_response.strip(),
        token_count=len(full_response.split()), # Mock token count
        round_number=round_number,
        phase=phase
    )
    db.add(assistant_msg)
    
    log_ai_usage(
        db=db,
        user_id=user_id,
        session_id=session_id,
        round_number=round_number,
        phase=phase,
        prompt_text=prompt,
        response_text=full_response.strip(),
        input_token_count=user_msg.token_count,
        output_token_count=assistant_msg.token_count,
        latency_ms=10
    )
    
    conversation.message_count += 1
    db.commit()
