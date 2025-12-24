"""
Document model for MongoDB
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentQuality(str, Enum):
    VALID = "valid"
    DUPLICATE = "duplicate"
    OUTDATED = "outdated"
    LOW_QUALITY = "low_quality"
    INVALID = "invalid"

class Document(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    batch_id: str = Field(..., description="Parent batch ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Storage path")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA256 hash for duplicate detection")
    mime_type: str = Field(..., description="MIME type")
    
    # Processing status
    status: str = Field(default="uploaded")
    processing_plan: Optional[Dict[str, Any]] = None
    
    # Preprocessing results
    elements: Optional[List[Dict[str, Any]]] = None
    page_images: Optional[List[str]] = None  # Paths to page images
    
    # Classification results
    doc_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_evidence: Optional[Dict[str, Any]] = None
    
    # Extraction results
    extracted_data: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None
    extraction_evidence: Optional[List[Dict[str, Any]]] = None
    
    # Quality assessment
    quality_flags: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = None
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_001",
                "batch_id": "batch_2024_001",
                "filename": "faculty_list.pdf",
                "doc_type": "faculty_list",
                "classification_confidence": 0.92
            }
        }

