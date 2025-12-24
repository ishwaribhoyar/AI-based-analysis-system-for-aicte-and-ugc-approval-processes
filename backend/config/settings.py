"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # MongoDB (supports both MONGODB_URL and MONGODB_URI)
    MONGODB_URL: Optional[str] = None
    MONGODB_URI: Optional[str] = None  # Alternative name for compatibility
    MONGODB_DB_NAME: str = "smart_approval_ai"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_PRIMARY: str = "gpt-5-nano"  # Primary model for classification, extraction, and chatbot
    OPENAI_MODEL_FALLBACK: str = "gpt-5-mini"  # Fallback model for JSON validation errors
    
    # Unstructured-IO
    UNSTRUCTURED_API_KEY: Optional[str] = None
    UNSTRUCTURED_LOCAL: bool = True
    
    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    REPORTS_DIR: str = "storage/reports"
    EVIDENCE_DIR: str = "storage/evidence"
    # Maximum single file size (safety limit) - 50 MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    
    # Processing
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.7
    EXTRACTION_RETRY_LIMIT: int = 3
    CHUNK_SIZE: int = 4000
    CHUNK_OVERLAP: int = 200
    
    # API Security
    API_TOKEN: Optional[str] = None
    
    class Config:
        # Look for .env in project root (parent of backend directory)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use MONGODB_URI if MONGODB_URL is not set
        if not self.MONGODB_URL and self.MONGODB_URI:
            self.MONGODB_URL = self.MONGODB_URI
        elif not self.MONGODB_URL:
            self.MONGODB_URL = "mongodb://localhost:27017/"

settings = Settings()
