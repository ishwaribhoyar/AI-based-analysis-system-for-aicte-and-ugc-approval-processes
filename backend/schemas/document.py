"""
Pydantic schemas for document operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str

class DocumentResponse(BaseModel):
    document_id: str
    batch_id: str
    filename: str
    file_size: int
    doc_type: Optional[str] = None  # Deprecated - kept for compatibility
    classification_confidence: Optional[float] = None  # Deprecated
    status: str
    quality_flags: List[str] = []  # Deprecated
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

