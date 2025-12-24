"""
Pydantic schemas for batch operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from models.batch import ReviewerMode, BatchStatus

class BatchCreate(BaseModel):
    mode: ReviewerMode = Field(..., description="UGC or AICTE mode")
    new_university: Optional[bool] = Field(False, description="True if new university (UGC only), False for renewal")
    institution_name: Optional[str] = None
    institution_code: Optional[str] = None
    academic_year: Optional[str] = None

class BatchResponse(BaseModel):
    batch_id: str
    mode: str  # Changed from ReviewerMode to str for compatibility
    status: str  # Changed from BatchStatus to str for compatibility
    created_at: str
    updated_at: str
    total_documents: int
    processed_documents: int
    institution_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class BatchListResponse(BaseModel):
    batches: List[BatchResponse]
    total: int

