"""
SQLite database connection and configuration
Temporary storage only - no historical data
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# SQLite database path
DB_DIR = Path(__file__).parent.parent / "storage" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "temp_batches.db"

# Create engine
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Minimal SQLite Schema
class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(String, primary_key=True)  # batch_id
    mode = Column(String)  # "ugc" or "aicte"
    new_university = Column(Integer, default=0)  # 0 = renewal, 1 = new university (for UGC only)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="created")
    errors = Column(JSON, nullable=True)  # Processing errors
    
    # Results stored as JSON (temporary)
    sufficiency_result = Column(JSON, nullable=True)
    kpi_results = Column(JSON, nullable=True)
    compliance_results = Column(JSON, nullable=True)
    trend_results = Column(JSON, nullable=True)
    approval_classification = Column(JSON, nullable=True)
    approval_readiness = Column(JSON, nullable=True)
    unified_report = Column(JSON, nullable=True)

class Block(Base):
    __tablename__ = "blocks"
    
    id = Column(String, primary_key=True)  # block_id
    batch_id = Column(String, index=True)
    block_type = Column(String, index=True)
    data = Column(JSON)  # extracted_data
    confidence = Column(Float, default=0.0)
    extraction_confidence = Column(Float, default=0.0)
    evidence_snippet = Column(Text)
    evidence_page = Column(Integer, nullable=True)
    source_doc = Column(String)  # filename
    
    # Quality flags
    is_outdated = Column(Integer, default=0)  # 0 or 1
    is_low_quality = Column(Integer, default=0)
    is_invalid = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class File(Base):
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)  # file_id
    batch_id = Column(String, index=True)
    filename = Column(String)
    filepath = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"
    
    id = Column(String, primary_key=True)
    batch_id = Column(String, index=True)
    severity = Column(String)  # "low", "medium", "high"
    message = Column(Text)
    title = Column(String)
    reason = Column(Text)
    recommendation = Column(Text, nullable=True)


class ApprovalClassification(Base):
    __tablename__ = "approval_classification"
    
    id = Column(String, primary_key=True)
    batch_id = Column(String, index=True)
    category = Column(String)  # aicte, ugc, mixed
    subtype = Column(String)   # new, renewal, unknown
    signals = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ApprovalRequiredDocument(Base):
    __tablename__ = "approval_required_documents"
    
    id = Column(String, primary_key=True)
    batch_id = Column(String, index=True)
    category = Column(String)
    required_key = Column(String)
    present = Column(Integer, default=0)  # 0/1
    confidence = Column(Float, default=0.0)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ComparisonCache(Base):
    __tablename__ = "comparison_cache"
    
    id = Column(String, primary_key=True)
    compare_key = Column(String, unique=True, index=True)
    batch_ids = Column(Text)  # comma-separated list
    payload = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PipelineCache(Base):
    """
    Generic pipeline cache for expensive steps (embeddings, KPIs, unified report, etc.).
    Cached payloads are JSON blobs with a simple TTL-based expiry.
    """
    __tablename__ = "pipeline_cache"

    id = Column(String, primary_key=True)
    cache_key = Column(String, unique=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)


class HistoricalKPI(Base):
    """Historical AICTE/UGC national KPI benchmarks by year."""
    __tablename__ = "historical_kpis"
    
    year = Column(Integer, primary_key=True)
    metrics = Column(JSON, nullable=False)  # avg_fsr, avg_infra, etc.
    source = Column(String, default="AICTE/UGC")  # Data source
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DocumentHashCache(Base):
    """Cache of document hashes for deduplication."""
    __tablename__ = "document_hash_cache"
    
    id = Column(String, primary_key=True)
    batch_id = Column(String, index=True)
    file_hash = Column(String, index=True)  # SHA256 hash
    filename = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Helpful composite indexes for performance
Index("idx_blocks_batch_type", Block.batch_id, Block.block_type)
Index("idx_compliance_flags_batch", ComplianceFlag.batch_id)
Index("idx_approval_required_docs_batch", ApprovalRequiredDocument.batch_id)
Index("idx_batch_status", Batch.status)

# Create tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info(f"SQLite database initialized at {DB_PATH}")

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, caller should close

def close_db(db: Session):
    """Close database session"""
    db.close()

# Initialize on import
init_db()
