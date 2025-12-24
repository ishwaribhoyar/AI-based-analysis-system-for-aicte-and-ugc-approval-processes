"""
Report generation router - SQLite version
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from schemas.reports import ReportGenerateRequest, ReportGenerateResponse
from services.report_generator import ReportGenerator
from config.database import get_db, Batch, close_db
from config.settings import settings
from datetime import datetime
import os

router = APIRouter()
report_generator = ReportGenerator()

@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(request: ReportGenerateRequest):
    """Generate PDF report for a batch"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == request.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if batch.status != "completed":
            raise HTTPException(status_code=400, detail="Batch processing not completed")
        
        # Generate report
        report_path = report_generator.generate_report(
            request.batch_id,
            include_evidence=request.include_evidence,
            include_trends=request.include_trends,
            report_type=request.report_type,
        )
        
        download_url = f"/reports/{os.path.basename(report_path)}"
        
        return ReportGenerateResponse(
            batch_id=request.batch_id,
            report_path=report_path,
            download_url=download_url,
            generated_at=datetime.utcnow().isoformat()
        )
    finally:
        close_db(db)

@router.get("/download/{batch_id}")
def download_report(batch_id: str):
    """Download generated report"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Find report file
        report_filename = f"report_{batch_id}.pdf"
        report_path = os.path.join(settings.REPORTS_DIR, report_filename)
        
        if not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail="Report not generated")
        
        return FileResponse(
            report_path,
            media_type="application/pdf",
            filename=report_filename
        )
    finally:
        close_db(db)
