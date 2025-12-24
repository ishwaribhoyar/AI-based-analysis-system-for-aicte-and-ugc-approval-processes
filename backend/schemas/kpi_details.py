"""
KPI Detail Breakdown schemas.
Contains models for parameter-level breakdown of each KPI.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ParameterBreakdown(BaseModel):
    """A single parameter contributing to a KPI."""
    parameter_name: str
    display_name: str
    raw_value: Optional[Any] = None
    normalized_value: Optional[float] = None
    unit: str = ""
    weight: float = 0.0
    score: float = 0.0
    contribution: float = 0.0  # weight * score / 100
    missing: bool = False
    note: str = ""


class FormulaStep(BaseModel):
    """A step in the KPI computation formula."""
    step_number: int
    description: str
    formula: str
    result: Optional[float] = None


class KPIBreakdown(BaseModel):
    """Complete breakdown for a single KPI."""
    kpi_key: str
    kpi_name: str
    final_score: float
    
    # Parameters
    parameters: List[ParameterBreakdown] = Field(default_factory=list)
    
    # Formula
    formula_steps: List[FormulaStep] = Field(default_factory=list)
    formula_text: str = ""
    
    # Status
    missing_parameters: List[str] = Field(default_factory=list)
    data_quality: str = "complete"  # complete, partial, insufficient
    confidence: float = 1.0


class KPIDetailsResponse(BaseModel):
    """Full KPI details for a batch."""
    batch_id: str
    institution_name: str
    mode: str
    
    # Individual KPI breakdowns
    fsr: Optional[KPIBreakdown] = None
    infrastructure: Optional[KPIBreakdown] = None
    placement: Optional[KPIBreakdown] = None
    lab_compliance: Optional[KPIBreakdown] = None
    overall: Optional[KPIBreakdown] = None
