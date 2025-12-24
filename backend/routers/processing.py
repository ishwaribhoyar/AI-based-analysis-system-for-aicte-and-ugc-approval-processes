"""
Processing pipeline router - SQLite version
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from schemas.processing import ProcessingStatusResponse, ProcessingStartRequest, ProcessingStartResponse
from pipelines.block_processing_pipeline import BlockProcessingPipeline
from config.database import get_db, Batch, File, close_db
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline = BlockProcessingPipeline()

@router.post("/start", response_model=ProcessingStartResponse)
def start_processing(
    request: ProcessingStartRequest,
    background_tasks: BackgroundTasks
):
    """Start processing a batch"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == request.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        current_status = batch.status
        if current_status in ["processing", "completed"]:
            return ProcessingStartResponse(
                batch_id=request.batch_id,
                status=current_status,
                message=f"Batch is already {current_status}"
            )
        
        # Start processing in background thread
        def run_pipeline():
            try:
                pipeline.process_batch(request.batch_id)
            except Exception as e:
                import traceback
                full_traceback = traceback.format_exc()
                error_msg = f"{str(e)}: {full_traceback}"
                logger.error(f"Pipeline error: {error_msg}")
                print(f"FULL ERROR TRACEBACK:\n{full_traceback}")  # Print to console for debugging
                db_inner = get_db()
                batch_inner = db_inner.query(Batch).filter(Batch.id == request.batch_id).first()
                if batch_inner:
                    batch_inner.status = "failed"
                    # Store both short error and full traceback
                    batch_inner.errors = [str(e), full_traceback[:500]]  # Store error + first 500 chars of traceback
                db_inner.commit()
                close_db(db_inner)
        
        thread = threading.Thread(target=run_pipeline)
        thread.daemon = True
        thread.start()
        
        batch.status = "processing"
        db.commit()
        
        return ProcessingStartResponse(
            batch_id=request.batch_id,
            status="processing",
            message="Processing started"
        )
    finally:
        close_db(db)

@router.get("/status/{batch_id}", response_model=ProcessingStatusResponse)
def get_processing_status(batch_id: str):
    """Get processing status for a batch"""
    if batch_id == "undefined" or not batch_id:
        raise HTTPException(status_code=400, detail="Invalid batch_id")
    
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        file_count = db.query(File).filter(File.batch_id == batch_id).count()
        
        # Calculate progress based on current stage
        stage_progress_map = {
            "created": 0,
            "docling_parsing": 10,
            "ocr_fallback": 15,               # NEW: OCR fallback for scanned documents
            "section_extraction": 20,          # NEW: Section keyword extraction
            "classify_approval": 25,
            "snippet_extraction": 28,
            "one_shot_extraction": 40,
            "block_mapping": 50,               # NEW: Mapping blocks to schema
            "storing_blocks": 55,
            "quality_check": 60,
            "sufficiency": 70,
            "kpi_scoring": 80,
            "compliance": 85,
            "approval_classification": 88,     # NEW: Approval classification
            "approval_readiness": 92,
            "trend_analysis": 96,
            "completed": 100,
            "failed": 0
        }
        progress = stage_progress_map.get(batch.status, 0)
        
        stage_map = {
            "created": "Ready",
            "docling_parsing": "Extracting using Docling...",
            "ocr_fallback": "Running OCR on scanned pages...",        # NEW
            "section_extraction": "Extracting relevant sections...",  # NEW
            "classify_approval": "Classifying approval category...",
            "snippet_extraction": "Filtering block snippets...",
            "one_shot_extraction": "One-shot AI extraction...",
            "block_mapping": "Mapping blocks to schema...",            # NEW
            "storing_blocks": "Storing blocks...",
            "quality_check": "Quality Check",
            "sufficiency": "Sufficiency",
            "kpi_scoring": "Running KPI engine...",
            "compliance": "Compliance Check",
            "approval_classification": "Classifying approval type...", # NEW
            "approval_readiness": "Approval readiness...",
            "trend_analysis": "Trend Analysis",
            "completed": "Completed",
            "failed": "Failed"
        }
        current_stage = stage_map.get(batch.status, batch.status)
        
        return ProcessingStatusResponse(
            batch_id=batch_id,
            status=batch.status,
            current_stage=current_stage,
            progress=round(progress, 2),
            total_documents=file_count,
            processed_documents=file_count if batch.status == "completed" else 0,
            errors=batch.errors if hasattr(batch, 'errors') and batch.errors else []
        )
    finally:
        close_db(db)


@router.get("/logs/{batch_id}")
async def stream_processing_logs(batch_id: str):
    """
    Stream processing logs via Server-Sent Events (SSE).
    Returns real-time status updates for the processing pipeline.
    """
    import asyncio
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        last_status = None
        poll_count = 0
        max_polls = 300  # 5 minutes max (300 * 1 second)
        
        while poll_count < max_polls:
            db = get_db()
            try:
                batch = db.query(Batch).filter(Batch.id == batch_id).first()
                
                if not batch:
                    yield f"data: {{\"event\": \"error\", \"message\": \"Batch not found\"}}\n\n"
                    break
                
                # Send update if status changed
                if batch.status != last_status:
                    last_status = batch.status
                    
                    # Calculate progress
                    stage_progress_map = {
                        "created": 0, "docling_parsing": 10, "ocr_fallback": 15,
                        "section_extraction": 20, "classify_approval": 25, "snippet_extraction": 28,
                        "one_shot_extraction": 40, "block_mapping": 50, "storing_blocks": 55,
                        "quality_check": 60, "sufficiency": 70, "kpi_scoring": 80,
                        "compliance": 85, "approval_classification": 88, "approval_readiness": 92,
                        "trend_analysis": 96, "completed": 100, "failed": 0
                    }
                    progress = stage_progress_map.get(batch.status, 0)
                    
                    import json
                    event_data = json.dumps({
                        "event": "status_update",
                        "status": batch.status,
                        "progress": progress,
                        "timestamp": datetime.now().isoformat()
                    })
                    yield f"data: {event_data}\n\n"
                
                # Exit on terminal states
                if batch.status in ["completed", "failed"]:
                    yield f"data: {{\"event\": \"done\", \"status\": \"{batch.status}\"}}\n\n"
                    break
                    
            finally:
                close_db(db)
            
            poll_count += 1
            await asyncio.sleep(1)  # Poll every 1 second
        
        # Timeout message
        if poll_count >= max_polls:
            yield f"data: {{\"event\": \"timeout\", \"message\": \"Max polling time exceeded\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
