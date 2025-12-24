"""
File upload router - SQLite version
Temporary storage only
"""

from fastapi import APIRouter, HTTPException, UploadFile, File as FastAPIFile, Form
from typing import List
from schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from config.database import get_db, File, Batch, close_db
from config.settings import settings
from utils.id_generator import generate_document_id
from utils.file_utils import save_uploaded_file, get_mime_type
from datetime import datetime, timezone
import shutil
from pathlib import Path

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    batch_id: str = Form(...),
    file: UploadFile = FastAPIFile(...)
):
    """Upload a file to a batch - PDF only (or JPG/PNG which will be wrapped in PDF)"""
    import logging
    logger = logging.getLogger(__name__)
    
    db = None
    try:
        # Verify batch exists
        db = get_db()
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check file extension - PDF, JPG, PNG, Excel, CSV, Word allowed
        filename_lower = file.filename.lower()
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.csv', '.docx']
        file_ext = Path(filename_lower).suffix
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Allowed file types: PDF, JPG, PNG, Excel (.xlsx, .xls), CSV, Word (.docx). Received: {file_ext}."
            )
        
        # Save file and calculate size simultaneously (chunked reading)
        file_size = 0
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        # Save file in chunks to avoid memory issues
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.MAX_FILE_SIZE:
                    # Clean up partial file
                    if file_path.exists():
                        file_path.unlink()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB"
                    )
                f.write(chunk)
        
        if file_size == 0:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create file record
        file_id = generate_document_id()
        
        file_record = File(
            id=file_id,
            batch_id=batch_id,
            filename=file.filename,
            filepath=str(file_path),
            file_size=file_size,
            uploaded_at=datetime.now(timezone.utc)
        )
        
        db.add(file_record)
        db.commit()
        
        logger.info(f"Successfully uploaded file {file.filename} ({file_size} bytes) to batch {batch_id}")
        
        return DocumentUploadResponse(
            document_id=file_id,
            filename=file.filename,
            file_size=file_size,
            status="uploaded"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        # Clean up partial file if it exists
        if 'file_path' in locals() and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    finally:
        if db:
            close_db(db)


@router.post("/{batch_id}/upload", response_model=DocumentUploadResponse)
async def upload_document_with_path(
    batch_id: str,
    file: UploadFile = FastAPIFile(...)
):
    """
    Alias endpoint for POST /api/documents/{batch_id}/upload.
    Uses batch_id from URL path parameter.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db = None
    try:
        # Verify batch exists
        db = get_db()
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check file extension - PDF, JPG, PNG, Excel, CSV, Word allowed
        filename_lower = file.filename.lower()
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.csv', '.docx']
        file_ext = Path(filename_lower).suffix
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Allowed file types: PDF, JPG, PNG, Excel (.xlsx, .xls), CSV, Word (.docx). Received: {file_ext}."
            )
        
        # Read file content in chunks to check size and save efficiently
        file_size = 0
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        # Save file and calculate size simultaneously
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.MAX_FILE_SIZE:
                    # Clean up partial file
                    if file_path.exists():
                        file_path.unlink()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB"
                    )
                f.write(chunk)
        
        if file_size == 0:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create file record
        file_id = generate_document_id()
        
        file_record = File(
            id=file_id,
            batch_id=batch_id,
            filename=file.filename,
            filepath=str(file_path),
            file_size=file_size,
            uploaded_at=datetime.now(timezone.utc)
        )
        
        db.add(file_record)
        db.commit()
        
        logger.info(f"Successfully uploaded file {file.filename} ({file_size} bytes) to batch {batch_id}")
        
        return DocumentUploadResponse(
            document_id=file_id,
            filename=file.filename,
            file_size=file_size,
            status="uploaded"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        # Clean up partial file if it exists
        if 'file_path' in locals() and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    finally:
        if db:
            close_db(db)

@router.get("/batch/{batch_id}", response_model=DocumentListResponse)
def list_documents(batch_id: str):
    """List all files in a batch"""
    db = get_db()
    
    try:
        files = db.query(File).filter(File.batch_id == batch_id).all()
        
        doc_responses = [
            DocumentResponse(
                document_id=f.id,
                batch_id=f.batch_id,
                filename=f.filename,
                file_size=f.file_size,
                doc_type=None,  # No document types
                classification_confidence=None,
                status="uploaded",
                quality_flags=[]
            )
            for f in files
        ]
        
        return DocumentListResponse(documents=doc_responses, total=len(doc_responses))
    finally:
        close_db(db)

@router.delete("/{document_id}")
def delete_document(document_id: str):
    """Delete a file"""
    db = get_db()
    
    try:
        file_record = db.query(File).filter(File.id == document_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file
        import os
        if os.path.exists(file_record.filepath):
            os.remove(file_record.filepath)
        
        # Delete record
        db.delete(file_record)
        db.commit()
        
        return {"message": "File deleted successfully"}
    finally:
        close_db(db)
