from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat
from typing import List, Dict, Any, Optional, Literal
from pydantic import Field
from datetime import datetime
from .domain import MilitaryPosture, PhaseEnum, RoundStatus, ResourceType

class CompanyBase(BaseModel):
    name: str
    
class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    nation_id: int
    revenue: float
    cogs: float
    gross_margin: float
    net_profit: float
    cash: float
    market_share: float
    products: Dict[str, Any]
    supply_chain_config: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class ResourceBase(BaseModel):
    type: ResourceType
    production_rate: float
    stockpile: float
    depletion_rate: float

class ResourceCreate(ResourceBase):
    pass

class Resource(ResourceBase):
    id: int
    nation_id: int

    model_config = ConfigDict(from_attributes=True)

class NationBase(BaseModel):
    name: str
    archetype: Optional[str] = None

class NationCreate(NationBase):
    pass

class Nation(NationBase):
    id: int
    session_id: int
    gdp: float
    cpi: float
    inflation: float
    unemployment: float
    approval_rating: float
    trade_balance: float
    treasury: float
    military_atk: int
    military_def: int
    policies: Dict[str, Any]
    
    companies: List[Company] = Field(default_factory=list)
    resources: List[Resource] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class DecisionBase(BaseModel):
    player_type: str
    entity_id: int
    decision_data: Dict[str, Any]

class DecisionCreate(DecisionBase):
    pass


class PresidentDecisionData(BaseModel):
    """Authoritative presidential controls, including Phase 3 readiness inputs."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    government_spending: float = Field(default=0.0, ge=0.0)
    tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    income_tax: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tariffs: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    immigration: Optional[float] = Field(default=None, ge=-0.05, le=0.05)
    resource_consumption: Dict[str, float] = Field(default_factory=dict)
    military_posture: MilitaryPosture = MilitaryPosture.DEFEND
    military_investment: float = Field(default=0.0, ge=0.0, le=1000000)
    emergency_preparedness_investment: float = Field(default=0.0, ge=0.0, le=1000000)


class PresidentialReadinessData(BaseModel):
    """Phase 3 fields that can be saved without replacing fiscal policy."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    military_posture: MilitaryPosture = MilitaryPosture.DEFEND
    military_investment: float = Field(default=0.0, ge=0.0, le=1000000)
    emergency_preparedness_investment: float = Field(default=0.0, ge=0.0, le=1000000)


class SourcingDecisionData(BaseModel):
    """One authoritative resource order submitted by a company."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    resource_type: ResourceType
    supplier_nation_id: int = Field(gt=0)
    quantity: float = Field(gt=0.0, le=1000000)
    mode: Literal["sea", "river", "rail", "air"] = "rail"


class CompanyDecisionData(BaseModel):
    """The supported Phase 1 company controls."""

    model_config = ConfigDict(extra="forbid")

    price: Optional[float] = Field(default=None, gt=0.0)
    headcount: int = Field(default=0, ge=0, le=1000000)
    production_units: NonNegativeFloat = Field(default=1.0, le=1000000)
    rnd_investment: NonNegativeFloat = Field(default=0.0, le=1000000)
    sourcing: List[SourcingDecisionData] = Field(default_factory=list, max_length=6)

class Decision(DecisionBase):
    id: int
    round_id: int
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoundBase(BaseModel):
    number: int
    status: RoundStatus
    events: List[Dict[str, Any]]

class RoundCreate(RoundBase):
    pass

class Round(RoundBase):
    id: int
    session_id: int
    decisions: List[Decision] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class GameSessionBase(BaseModel):
    seed: str
    
class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: int
    map_snapshot: Optional[Dict[str, Any]] = None
    current_round: int
    phase: PhaseEnum
    created_at: datetime
    status: str
    
    nations: List[Nation] = Field(default_factory=list)
    rounds: List[Round] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class MapSnapshot(BaseModel):
    id: int
    session_id: int
    validated_map_json: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
