from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from pydantic import Field
from datetime import datetime
from .domain import PhaseEnum, RoundStatus, ResourceType

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
