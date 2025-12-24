"""
Pydantic schemas for report operations
"""

from pydantic import BaseModel, Field

class ReportGenerateRequest(BaseModel):
    batch_id: str
    include_evidence: bool = True
    include_trends: bool = True
    report_type: str = Field(default="standard", description="standard|aicte|ugc|unified")

class ReportGenerateResponse(BaseModel):
    batch_id: str
    report_path: str
    download_url: str
    generated_at: str

