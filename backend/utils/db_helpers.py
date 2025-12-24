"""
Database helper utilities - SQLite version
"""

from fastapi import HTTPException
from config.database import get_db

def get_db_or_error():
    """Get database session or raise HTTP 503 error"""
    try:
        return get_db()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection unavailable: {str(e)}"
        )
