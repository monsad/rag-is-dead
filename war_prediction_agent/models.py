from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SourceType(str, Enum):
    NEWS = "news"
    MILITARY = "military"
    SOCIAL_MEDIA = "social_media"
    INTELLIGENCE = "intelligence"

class DataPoint(BaseModel):
    id: str
    source: str
    source_type: SourceType
    title: str
    content: str
    url: Optional[str] = None
    timestamp: datetime
    relevance_score: float = 0.0
    sentiment: float = 0.0
    keywords: List[str] = []

class ConflictIndicator(BaseModel):
    name: str
    value: float
    weight: float
    description: str

class RegionAnalysis(BaseModel):
    region: str
    risk_score: float
    risk_level: RiskLevel
    indicators: List[ConflictIndicator]
    active_conflicts: List[str]
    data_points_analyzed: int

class PredictionRequest(BaseModel):
    regions: Optional[List[str]] = None
    include_social_media: bool = True
    lookback_hours: int = 24

class PredictionResponse(BaseModel):
    timestamp: datetime
    global_risk_score: float
    global_risk_level: RiskLevel
    regional_analyses: List[RegionAnalysis]
    key_events: List[DataPoint]
    confidence: float
    reasoning: str
    sources_analyzed: int

class AgentState(BaseModel):
    """State for LangGraph agent"""
    data_collected: List[DataPoint] = []
    analyzed_data: Dict = {}
    risk_scores: Dict[str, float] = {}
    final_prediction: Optional[PredictionResponse] = None
    iteration: int = 0
    errors: List[str] = []