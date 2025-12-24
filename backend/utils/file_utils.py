"""
File utility functions
"""

import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
from fastapi import UploadFile

async def save_uploaded_file(
    file: UploadFile,
    batch_id: str,
    upload_dir: str
) -> Tuple[str, str, int]:
    """
    Save uploaded file and return (file_path, file_hash, file_size)
    """
    # Create batch directory
    batch_dir = Path(upload_dir) / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = batch_dir / unique_filename
    
    # Save file
    file_size = 0
    hasher = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):
            await f.write(chunk)
            file_size += len(chunk)
            hasher.update(chunk)
    
    file_hash = hasher.hexdigest()
    
    return str(file_path), file_hash, file_size

def get_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_mime_type(filename: str) -> str:
    """Get MIME type from filename"""
    ext = Path(filename).suffix.lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.zip': 'application/zip'
    }
    return mime_types.get(ext, 'application/octet-stream')

def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    ext = Path(filename).suffix.lower()
    return ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

def is_scanned_document(file_path: str) -> bool:
    """Heuristic to detect if document is scanned (simplified)"""
    # In production, use OCR confidence or image analysis
    # For now, return False - will be determined during preprocessing
    return False

