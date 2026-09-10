# pyrefly: ignore [missing-import]
from sqlalchemy import CheckConstraint, Column, Integer, String, Float, ForeignKey, JSON, DateTime, Enum, UniqueConstraint
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
import enum
try:
    from ..database import Base
except ImportError:
    from database import Base

class PhaseEnum(str, enum.Enum):
    PLANNING = "planning"
    PRESIDENTIAL = "presidential"
    COMPANY = "company"
    PROCESSING = "processing"
    COMPLETE = "complete"

class RoundStatus(str, enum.Enum):
    PLANNING = "planning"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETE = "complete"

class ResourceType(str, enum.Enum):
    ENERGY = "Energy"
    MINERALS = "Minerals"
    AGRICULTURE = "Agriculture"
    TECHNOLOGY = "Technology"
    LABOR = "Labor"
    CAPITAL = "Capital"


class MilitaryPosture(str, enum.Enum):
    DEFEND = "defend"
    PATROL = "patrol"
    RECONNAISSANCE = "reconnaissance"


class EventType(str, enum.Enum):
    NATURAL_DISASTER = "natural_disaster"


class EventScope(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    seed = Column(String, nullable=False)
    map_snapshot = Column(JSON, nullable=True) # Validated map state
    current_round = Column(Integer, default=1)
    phase = Column(Enum(PhaseEnum), default=PhaseEnum.PLANNING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active")
    lobby_join_code = Column(String, nullable=True, unique=True, index=True)
    lobby_code_revoked = Column(Integer, default=0, nullable=False)
    presidential_deadline_at = Column(DateTime(timezone=True), nullable=True)
    company_deadline_at = Column(DateTime(timezone=True), nullable=True)
    phase_duration_seconds = Column(Integer, default=172800, nullable=False)

    rounds = relationship("Round", back_populates="session")
    nations = relationship("Nation", back_populates="session")
    map_snapshots = relationship("MapSnapshot", back_populates="session", cascade="all, delete-orphan")
    memberships = relationship("GameMembership", back_populates="session", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    is_instructor = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memberships = relationship("GameMembership", back_populates="user", cascade="all, delete-orphan")
    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="auth_sessions")


class GameMembership(Base):
    """A player's role and optional assigned entity in one game session."""

    __tablename__ = "game_memberships"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False, default="player")
    entity_id = Column(Integer, nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GameSession", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_membership_user_per_session"),
        UniqueConstraint("session_id", "role", "entity_id", name="uq_membership_seat_per_session"),
    )


class LobbyAudit(Base):
    """Append-only record of lobby-era naming and seat administration."""

    __tablename__ = "lobby_audit"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    before_value = Column(String, nullable=True)
    after_value = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DecisionDraft(Base):
    """Server-persisted editable draft for one seat in one open round."""

    __tablename__ = "decision_drafts"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    decision_data = Column(JSON, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("round_id", "player_type", "entity_id", name="uq_draft_entity_per_round"),
    )

class MapSnapshot(Base):
    __tablename__ = "map_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False, unique=True)
    validated_map_json = Column(JSON, nullable=False)

    session = relationship("GameSession", back_populates="map_snapshots")

class Nation(Base):
    __tablename__ = "nations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    name = Column(String, nullable=False)
    archetype = Column(String)
    
    # Economy Stats
    gdp = Column(Float, default=0.0)
    cpi = Column(Float, default=100.0)
    inflation = Column(Float, default=0.0)
    unemployment = Column(Float, default=5.0)
    approval_rating = Column(Float, default=60.0)
    trade_balance = Column(Float, default=0.0)
    treasury = Column(Float, default=1000.0) # Starting capital
    
    # Military Stats
    military_atk = Column(Integer, default=1)
    military_def = Column(Integer, default=1)
    military_readiness = Column(Float, default=0.0, nullable=False)
    emergency_preparedness_balance = Column(Float, default=0.0, nullable=False)
    
    # Policies (JSON for flexible schema)
    policies = Column(JSON, default=dict)

    session = relationship("GameSession", back_populates="nations")
    companies = relationship("Company", back_populates="nation")
    resources = relationship("Resource", back_populates="nation")

    __table_args__ = (
        CheckConstraint("military_readiness >= 0", name="ck_nation_military_readiness_nonnegative"),
        CheckConstraint("emergency_preparedness_balance >= 0", name="ck_nation_emergency_fund_nonnegative"),
    )

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    nation_id = Column(Integer, ForeignKey("nations.id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Financials
    revenue = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    gross_margin = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    cash = Column(Float, default=500.0)
    market_share = Column(Float, default=0.0)
    
    # Operations
    products = Column(JSON, default=dict)
    supply_chain_config = Column(JSON, default=dict)

    nation = relationship("Nation", back_populates="companies")

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    nation_id = Column(Integer, ForeignKey("nations.id"), nullable=False)
    type = Column(Enum(ResourceType), nullable=False)
    
    production_rate = Column(Float, default=0.0)
    stockpile = Column(Float, default=0.0)
    depletion_rate = Column(Float, default=0.0)

    nation = relationship("Nation", back_populates="resources")

class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    number = Column(Integer, nullable=False)
    status = Column(Enum(RoundStatus), default=RoundStatus.PLANNING, nullable=False)
    events = Column(JSON, default=list)
    results = Column(JSON, default=dict)

    session = relationship("GameSession", back_populates="rounds")
    decisions = relationship("Decision", back_populates="round")
    phase3_events = relationship("RoundEvent", back_populates="round", cascade="all, delete-orphan")
    effects = relationship("RoundEffect", back_populates="round", cascade="all, delete-orphan")

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_type = Column(String) # 'president' or 'company'
    entity_id = Column(Integer, nullable=False) # Nation ID or Company ID
    decision_data = Column(JSON, default=dict)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    submission_kind = Column(String, default="human", nullable=False)
    auto_reason = Column(String, nullable=True)

    round = relationship("Round", back_populates="decisions")

    __table_args__ = (
        UniqueConstraint("round_id", "player_type", "entity_id", name="uq_decision_entity_per_round"),
    )


class RoundEvent(Base):
    """One validated Phase 3 event scheduled for a round.

    Event definitions are catalog-backed in the API layer; this record stores
    the immutable selected instance and its deterministic inputs.
    """

    __tablename__ = "round_events"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False)
    target_nation_id = Column(Integer, ForeignKey("nations.id"), nullable=True, index=True)
    severity = Column(Integer, nullable=False, default=1)
    event_data = Column(JSON, default=dict, nullable=False)
    source = Column(String, nullable=False, default="instructor")
    injected_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    round = relationship("Round", back_populates="phase3_events")
    recovery_funding = relationship("CompanyRecoveryFunding", back_populates="round_event", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("round_id", "event_type", "target_nation_id", name="uq_round_event_target"),
        CheckConstraint("severity BETWEEN 1 AND 3", name="ck_round_event_severity_range"),
    )


class RoundEffect(Base):
    """Append-only resolved effect for a completed round."""

    __tablename__ = "round_effects"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False, index=True)
    round_event_id = Column(Integer, ForeignKey("round_events.id"), nullable=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    effect_type = Column(String, nullable=False)
    scope = Column(Enum(EventScope), nullable=False, default=EventScope.PUBLIC)
    effect_data = Column(JSON, default=dict, nullable=False)
    reproducibility_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    round = relationship("Round", back_populates="effects")

    __table_args__ = (
        UniqueConstraint("round_id", "entity_type", "entity_id", "effect_type", name="uq_round_effect_entity_type"),
    )


class CompanyRecoveryFunding(Base):
    """Public and private recovery amounts allocated after a disaster."""

    __tablename__ = "company_recovery_funding"

    id = Column(Integer, primary_key=True, index=True)
    round_event_id = Column(Integer, ForeignKey("round_events.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    public_fund_amount = Column(Float, nullable=False, default=0.0)
    private_fund_amount = Column(Float, nullable=False, default=0.0)
    private_financing_cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    round_event = relationship("RoundEvent", back_populates="recovery_funding")

    __table_args__ = (
        UniqueConstraint("round_event_id", "company_id", name="uq_recovery_funding_company_event"),
        CheckConstraint("public_fund_amount >= 0", name="ck_recovery_public_fund_nonnegative"),
        CheckConstraint("private_fund_amount >= 0", name="ck_recovery_private_fund_nonnegative"),
        CheckConstraint("private_financing_cost >= 0", name="ck_recovery_financing_cost_nonnegative"),
    )
