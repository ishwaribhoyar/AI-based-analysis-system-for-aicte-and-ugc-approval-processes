"""
Batch management router - SQLite version
Temporary storage only
"""

from fastapi import APIRouter, HTTPException
from typing import List
from schemas.batch import BatchCreate, BatchResponse, BatchListResponse
from config.database import get_db, Batch, close_db
from utils.id_generator import generate_batch_id
from datetime import datetime, timezone

router = APIRouter()

@router.post("/", response_model=BatchResponse)
def create_batch(batch_data: BatchCreate):
    """Create a new batch"""
    db = get_db()
    
    try:
        batch_id = generate_batch_id(batch_data.mode.value)
        
        batch = Batch(
            id=batch_id,
            mode=batch_data.mode.value,
            new_university=1 if batch_data.new_university else 0,
            status="created",
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        return BatchResponse(
            batch_id=batch_id,
            mode=batch.mode,
            status=batch.status,
            created_at=batch.created_at.isoformat(),
            updated_at=batch.created_at.isoformat(),
            total_documents=0,
            processed_documents=0,
            institution_name=None
        )
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"Error creating batch: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")
    finally:
        close_db(db)


@router.post("/create", response_model=BatchResponse)
def create_batch_alias(batch_data: BatchCreate):
    """
    Alias endpoint for POST /api/batches/create to support frontend expectations.
    Delegates to the main SQLite batch creator.
    """
    try:
        return create_batch(batch_data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error in create_batch_alias: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")


@router.get("/list", response_model=List[BatchResponse])
def list_batches(filter: str = None):
    """
    List all batches.
    
    By default, only returns batches with processed_documents > 0 (evidence-driven).
    
    Optional filter parameter:
    - filter=all: Return all batches including empty ones
    - filter=valid: Only return completed batches with at least 1 document
    """
    db = get_db()
    
    try:
        from config.database import File, Block
        batches = db.query(Batch).order_by(Batch.created_at.desc()).all()
        
        result = []
        for batch in batches:
            file_count = db.query(File).filter(File.batch_id == batch.id).count()
            block_count = db.query(Block).filter(Block.batch_id == batch.id).count()
            
            # Default behavior: filter out batches with 0 processed documents (evidence-driven)
            if filter != "all":
                if file_count == 0 or block_count == 0:
                    continue
            
            # Apply additional filter if specified
            if filter == "valid":
                # Skip batches that are not completed or have 0 documents
                if batch.status != "completed" or file_count == 0:
                    continue
            
            result.append(BatchResponse(
                batch_id=batch.id,
                mode=batch.mode,
                status=batch.status,
                created_at=batch.created_at.isoformat() if batch.created_at else "",
                updated_at=batch.created_at.isoformat() if batch.created_at else "",
                total_documents=file_count,
                processed_documents=file_count if batch.status == "completed" else 0,
                institution_name=None
            ))
        
        return result
    except Exception as e:
        print(f"Error listing batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        close_db(db)

@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: str):
    """Get batch by ID"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        from config.database import File
        file_count = db.query(File).filter(File.batch_id == batch_id).count()
        
        return BatchResponse(
            batch_id=batch.id,
            mode=batch.mode,
            status=batch.status,
            created_at=batch.created_at.isoformat(),
            updated_at=batch.created_at.isoformat(),
            total_documents=file_count,
            processed_documents=file_count if batch.status == "completed" else 0,
            institution_name=None
        )
    finally:
        close_db(db)

@router.delete("/{batch_id}")
def delete_batch(batch_id: str):
    """Delete batch and associated data"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Delete associated data
        from config.database import Block, File, ComplianceFlag
        db.query(Block).filter(Block.batch_id == batch_id).delete()
        db.query(File).filter(File.batch_id == batch_id).delete()
        db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).delete()
        db.delete(batch)
        db.commit()
        
        return {"message": "Batch deleted successfully"}
    finally:
        close_db(db)
