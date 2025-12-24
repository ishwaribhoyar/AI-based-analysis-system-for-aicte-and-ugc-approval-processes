"""
SQLite Models - Temporary storage only
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()

# Models are defined in config/database.py
# This file is for Pydantic schemas for API responses

from pydantic import BaseModel, Field

class BatchResponse(BaseModel):
    """Batch response schema"""
    batch_id: str
    mode: str
    status: str
    created_at: str
    sufficiency_result: Optional[Dict[str, Any]] = None
    kpi_results: Optional[Dict[str, Any]] = None
    compliance_results: Optional[List[Dict[str, Any]]] = None

class BlockResponse(BaseModel):
    """Block response schema"""
    block_id: str
    batch_id: str
    block_type: str
    extracted_data: Dict[str, Any]
    confidence: float
    extraction_confidence: float
    evidence_snippet: str
    evidence_page: Optional[int] = None
    source_doc: str
    is_outdated: bool
    is_low_quality: bool
    is_invalid: bool

class ComplianceFlagResponse(BaseModel):
    """Compliance flag response schema"""
    flag_id: str
    batch_id: str
    severity: str
    title: str
    reason: str
    recommendation: Optional[str] = None

