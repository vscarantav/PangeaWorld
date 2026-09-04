from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
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

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    seed = Column(String, nullable=False)
    map_snapshot = Column(JSON, nullable=True) # Validated map state
    current_round = Column(Integer, default=1)
    phase = Column(Enum(PhaseEnum), default=PhaseEnum.PLANNING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active")

    rounds = relationship("Round", back_populates="session")
    nations = relationship("Nation", back_populates="session")
    map_snapshots = relationship("MapSnapshot", back_populates="session", cascade="all, delete-orphan")

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
    trade_balance = Column(Float, default=0.0)
    treasury = Column(Float, default=1000.0) # Starting capital
    
    # Military Stats
    military_atk = Column(Integer, default=1)
    military_def = Column(Integer, default=1)
    
    # Policies (JSON for flexible schema)
    policies = Column(JSON, default=dict)

    session = relationship("GameSession", back_populates="nations")
    companies = relationship("Company", back_populates="nation")
    resources = relationship("Resource", back_populates="nation")

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

    session = relationship("GameSession", back_populates="rounds")
    decisions = relationship("Decision", back_populates="round")

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_type = Column(String) # 'president' or 'company'
    entity_id = Column(Integer, nullable=False) # Nation ID or Company ID
    decision_data = Column(JSON, default=dict)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    round = relationship("Round", back_populates="decisions")

    __table_args__ = (
        UniqueConstraint("round_id", "player_type", "entity_id", name="uq_decision_entity_per_round"),
    )
