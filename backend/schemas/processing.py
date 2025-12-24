"""
Pydantic schemas for processing operations
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ProcessingStatusResponse(BaseModel):
    batch_id: str
    status: str
    current_stage: str
    progress: float
    total_documents: int
    processed_documents: int
    errors: List[str] = []

class ProcessingStartRequest(BaseModel):
    batch_id: str

class ProcessingStartResponse(BaseModel):
    batch_id: str
    status: str
    message: str

