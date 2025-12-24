"""
Batch model - Pydantic schemas for API (SQLite storage handled separately)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReviewerMode(str, Enum):
    UGC = "ugc"
    AICTE = "aicte"
    MIXED = "mixed"  # Combined AICTE + UGC evaluation

class BatchStatus(str, Enum):
    CREATED = "created"
    PREPROCESSING = "preprocessing"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    QUALITY_CHECK = "quality_check"
    SUFFICIENCY = "sufficiency"
    KPI_SCORING = "kpi_scoring"
    TREND_ANALYSIS = "trend_analysis"
    COMPLIANCE = "compliance"
    COMPLETED = "completed"
    FAILED = "failed"

# This is just for API schemas - actual storage is in SQLite
class Batch(BaseModel):
    batch_id: str = Field(..., description="Unique batch identifier")
    mode: ReviewerMode = Field(..., description="UGC or AICTE mode")
    status: BatchStatus = Field(default=BatchStatus.CREATED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Results (stored as JSON in SQLite)
    sufficiency_result: Optional[Dict[str, Any]] = None
    kpi_results: Optional[Dict[str, Any]] = None
    compliance_results: Optional[List[Dict[str, Any]]] = None
    trend_results: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_2024_001",
                "mode": "ugc",
                "status": "completed"
            }
        }
