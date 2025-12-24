"""
Information Block Models
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class BlockEvidence(BaseModel):
    """Evidence for a block extraction"""
    page: Optional[int] = None
    snippet: str = Field(..., description="Text snippet supporting the extraction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

class InformationBlock(BaseModel):
    """Information block extracted from a document chunk"""
    block_id: str = Field(..., description="Unique block identifier")
    batch_id: str = Field(..., description="Parent batch ID")
    document_id: str = Field(..., description="Source document ID")
    chunk_id: str = Field(..., description="Source chunk identifier")
    
    # Block identification
    block_type: str = Field(..., description="Type of information block (e.g., faculty_information)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    
    # Extracted data
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Extracted structured data")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Evidence
    evidence: List[BlockEvidence] = Field(default_factory=list, description="Evidence snippets")
    
    # Quality flags
    is_outdated: bool = Field(default=False, description="Block contains outdated information (>2 years)")
    is_low_quality: bool = Field(default=False, description="Block has low extraction confidence or insufficient text")
    is_invalid: bool = Field(default=False, description="Block contains logically invalid data")
    
    # Quality details
    outdated_reason: Optional[str] = None
    low_quality_reason: Optional[str] = None
    invalid_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "block_id": "block_001",
                "batch_id": "batch_2024_001",
                "document_id": "doc_001",
                "chunk_id": "chunk_001",
                "block_type": "faculty_information",
                "confidence": 0.92,
                "extracted_data": {
                    "faculty_count": 56,
                    "total_faculty": 56
                },
                "extraction_confidence": 0.88,
                "evidence": [
                    {
                        "page": 1,
                        "snippet": "The institute employs 56 faculty members...",
                        "confidence": 0.92
                    }
                ]
            }
        }

class BlockClassificationResult(BaseModel):
    """Result of semantic block classification"""
    blocks_detected: List[str] = Field(..., description="List of block types detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    snippet: str = Field(..., description="Supporting text snippet")
    page: Optional[int] = None

