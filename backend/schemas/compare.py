"""
Comparison schemas with institution-centric data structures.
Includes validation and skipped batch tracking.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from schemas.dashboard import KPICard, SufficiencyCard, ComplianceFlag, BlockCard


class SkippedBatch(BaseModel):
    """A batch that was excluded from comparison with reason."""
    batch_id: str
    reason: str  # "no_documents", "not_completed", "no_kpis", "missing_dashboard"


class InstitutionComparison(BaseModel):
    """Data for a single valid institution in comparison."""
    batch_id: str
    institution_name: str  # Real name only, no dummy IDs
    short_label: str = ""  # e.g., "SIT-24"
    academic_year: Optional[str] = None
    mode: str = ""  # aicte, ugc, mixed
    
    # KPI data - null for missing, never 0 as placeholder
    kpis: Dict[str, Optional[float]] = Field(default_factory=dict)
    
    # Summary metrics
    sufficiency_percent: float = 0.0
    compliance_count: int = 0
    overall_score: float = 0.0
    
    # Analysis
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class CategoryWinner(BaseModel):
    """Winner for a specific KPI category."""
    kpi_key: str
    kpi_name: str  # Readable name
    winner_batch_id: str
    winner_label: str  # Short label
    winner_value: float
    is_tie: bool = False
    tied_with: List[str] = Field(default_factory=list)


class ComparisonInterpretation(BaseModel):
    """Analysis and interpretation of comparison results."""
    best_overall_batch_id: str
    best_overall_label: str
    best_overall_name: str
    
    category_winners: List[CategoryWinner] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ComparisonResponse(BaseModel):
    """Full comparison response with clean, readable data."""
    # Valid institutions for comparison
    institutions: List[InstitutionComparison] = Field(default_factory=list)
    
    # Batches excluded from comparison with reasons
    skipped_batches: List[SkippedBatch] = Field(default_factory=list)
    
    # Comparison matrix (only for valid institutions)
    comparison_matrix: Dict[str, Dict[str, Optional[float]]] = Field(default_factory=dict)
    
    # Winner info with readable labels
    winner_institution: Optional[str] = None
    winner_label: Optional[str] = None
    winner_name: Optional[str] = None
    
    # Per-KPI winners
    category_winners: Dict[str, str] = Field(default_factory=dict)
    category_winners_labels: Dict[str, str] = Field(default_factory=dict)
    
    # Full interpretation
    interpretation: Optional[ComparisonInterpretation] = None
    
    # Validation status
    valid_for_comparison: bool = True
    validation_message: Optional[str] = None


class RankingInstitution(BaseModel):
    """Ranked institution with KPI breakdown."""
    batch_id: str
    name: str
    short_label: str
    ranking_score: float
    fsr_score: Optional[float] = None
    infrastructure_score: Optional[float] = None
    placement_index: Optional[float] = None
    lab_compliance_index: Optional[float] = None
    overall_score: Optional[float] = None
    mode: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class RankingResponse(BaseModel):
    """Top-N ranking response."""
    ranking_type: str
    top_n: int
    institutions: List[RankingInstitution] = Field(default_factory=list)
    insufficient_batches: List[SkippedBatch] = Field(default_factory=list)