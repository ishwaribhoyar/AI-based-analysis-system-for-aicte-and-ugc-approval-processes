"""
Pydantic schemas for dashboard data
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class KPICard(BaseModel):
    name: str
    value: Optional[float] = None  # Can be None for "Insufficient Data"
    label: str
    color: str = "blue"

class BlockCard(BaseModel):
    """Information block card for dashboard"""
    block_id: str
    block_type: str
    block_name: str
    is_present: bool
    is_outdated: bool
    is_low_quality: bool
    is_invalid: bool
    confidence: float
    extracted_fields_count: int
    evidence_snippet: Optional[str] = None
    evidence_page: Optional[int] = None
    source_doc: Optional[str] = None


class BlockWithData(BlockCard):
    """Extends BlockCard with the extracted data payload."""
    data: Dict[str, Any] = Field(default_factory=dict)


class SufficiencyCard(BaseModel):
    percentage: float
    present_count: int
    required_count: int
    missing_blocks: List[str]  # Changed from missing_documents
    penalty_breakdown: Dict[str, int]
    color: str  # red/yellow/green

class ComplianceFlag(BaseModel):
    severity: str  # low/medium/high
    title: str
    reason: str
    evidence_page: Optional[int] = None
    evidence_snippet: Optional[str] = None
    recommendation: Optional[str] = None

class TrendDataPoint(BaseModel):
    year: str
    kpi_name: str
    value: float


class ApprovalClassification(BaseModel):
    category: str
    subtype: str
    signals: List[str] = Field(default_factory=list)


class ApprovalReadiness(BaseModel):
    approval_category: str
    approval_readiness_score: float
    present: int
    required: int
    approval_missing_documents: List[str] = Field(default_factory=list)
    recommendation: str

class DashboardResponse(BaseModel):
    batch_id: str
    mode: str
    institution_name: Optional[str] = None
    kpi_cards: List[KPICard]
    # Simplified KPI map for consumers that expect direct values
    kpis: Dict[str, Optional[float]] = Field(default_factory=dict)
    block_cards: List[BlockCard]  # 10 information blocks
    # Blocks including the extracted data payload
    blocks: List[BlockWithData] = Field(default_factory=list)
    sufficiency: SufficiencyCard
    compliance_flags: List[ComplianceFlag]
    trend_data: List[TrendDataPoint]
    total_documents: int
    processed_documents: int
    approval_classification: Optional[ApprovalClassification] = None
    approval_readiness: Optional[ApprovalReadiness] = None

