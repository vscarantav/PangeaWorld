from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

try:
    from ..database import Base
except ImportError:
    from database import Base

class AIMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False) # e.g. "president" or "company"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_count = Column(Integer, default=0, nullable=False)

    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", "role", name="uq_ai_conversation_user_session_role"),
    )

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(Enum(AIMessageRole), nullable=False)
    content = Column(String, nullable=False)
    token_count = Column(Integer, default=0)
    round_number = Column(Integer, nullable=False)
    phase = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("AIConversation", back_populates="messages")

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    phase = Column(String, nullable=False)
    prompt_text = Column(String, nullable=False)
    response_text = Column(String, nullable=False)
    input_token_count = Column(Integer, default=0)
    output_token_count = Column(Integer, default=0)
    total_token_count = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    guardrail_flags = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
