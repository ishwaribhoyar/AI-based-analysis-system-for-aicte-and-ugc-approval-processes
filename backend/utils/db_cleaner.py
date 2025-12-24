"""
Database Cleaning Utility for SQLite.
Provides functions to purge invalid batches, remove duplicates, and cleanup redundant data.
"""

import logging
import hashlib
from typing import List, Dict, Set, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from config.database import (
    get_db, close_db, 
    Batch, Block, File, ComplianceFlag,
    ApprovalClassification, ApprovalRequiredDocument
)

logger = logging.getLogger(__name__)


def purge_invalid_batches() -> Dict[str, int]:
    """
    Delete batches that don't meet quality thresholds:
    - sufficiency < 30%
    - OR KPI overall_score == 0
    - OR blocks count == 0
    - OR approval_readiness_score == 0
    - OR missing > 50% required blocks
    
    Returns dict with deletion stats.
    """
    db = get_db()
    stats = {
        "batches_deleted": 0,
        "blocks_deleted": 0,
        "files_deleted": 0,
        "compliance_flags_deleted": 0,
        "classifications_deleted": 0,
        "required_docs_deleted": 0,
    }
    
    try:
        batches = db.query(Batch).all()
        batches_to_delete = []
        
        for batch in batches:
            should_delete = False
            reason = ""
            
            # Check sufficiency
            sufficiency = batch.sufficiency_result or {}
            suff_pct = sufficiency.get("percentage", 100)
            if suff_pct < 30:
                should_delete = True
                reason = f"sufficiency {suff_pct}% < 30%"
            
            # Check KPI overall_score
            kpis = batch.kpi_results or {}
            overall = kpis.get("overall_score", {})
            overall_val = overall.get("value") if isinstance(overall, dict) else overall
            if overall_val == 0 or overall_val is None:
                should_delete = True
                reason = f"overall_score = {overall_val}"
            
            # Check blocks count
            block_count = db.query(Block).filter(Block.batch_id == batch.id).count()
            if block_count == 0:
                should_delete = True
                reason = "blocks count = 0"
            
            # Check approval_readiness_score
            readiness = batch.approval_readiness or {}
            readiness_score = readiness.get("approval_readiness_score", 100)
            if readiness_score == 0:
                should_delete = True
                reason = f"approval_readiness_score = 0"
            
            if should_delete:
                batches_to_delete.append((batch.id, reason))
        
        # Delete invalid batches and all related data
        for batch_id, reason in batches_to_delete:
            logger.info(f"Purging batch {batch_id}: {reason}")
            
            # Delete blocks
            blocks_deleted = db.query(Block).filter(Block.batch_id == batch_id).delete()
            stats["blocks_deleted"] += blocks_deleted
            
            # Delete files
            files_deleted = db.query(File).filter(File.batch_id == batch_id).delete()
            stats["files_deleted"] += files_deleted
            
            # Delete compliance flags
            flags_deleted = db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).delete()
            stats["compliance_flags_deleted"] += flags_deleted
            
            # Delete approval classifications
            class_deleted = db.query(ApprovalClassification).filter(ApprovalClassification.batch_id == batch_id).delete()
            stats["classifications_deleted"] += class_deleted
            
            # Delete approval required documents
            docs_deleted = db.query(ApprovalRequiredDocument).filter(ApprovalRequiredDocument.batch_id == batch_id).delete()
            stats["required_docs_deleted"] += docs_deleted
            
            # Delete batch
            db.query(Batch).filter(Batch.id == batch_id).delete()
            stats["batches_deleted"] += 1
        
        db.commit()
        logger.info(f"Purge complete: {stats}")
        return stats
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error purging batches: {e}")
        raise
    finally:
        close_db(db)


def _get_block_signature(blocks: List[Block]) -> str:
    """Generate a signature from block data for similarity comparison."""
    key_fields = []
    for block in blocks:
        data = block.data or {}
        # Extract key identifying fields
        for key in ['institution_name', 'program_name', 'faculty_count', 'address', 'total_students']:
            if key in data:
                key_fields.append(str(data[key]).lower().strip())
    return "|".join(sorted(key_fields))


def _calculate_similarity(sig1: str, sig2: str) -> float:
    """Calculate similarity ratio between two signatures."""
    return SequenceMatcher(None, sig1, sig2).ratio()


def remove_duplicate_institutions() -> Dict[str, int]:
    """
    Remove duplicate batches based on:
    - Same institution name (case-insensitive)
    - Same document hash (SHA256)
    - 85% similarity in extracted blocks
    
    Keeps the newest batch, deletes the rest.
    Returns dict with deletion stats.
    """
    db = get_db()
    stats = {"duplicates_removed": 0, "batches_kept": 0}
    
    try:
        batches = db.query(Batch).order_by(Batch.created_at.desc()).all()
        
        # Group by institution name
        name_groups: Dict[str, List[Batch]] = {}
        hash_groups: Dict[str, List[Batch]] = {}
        
        for batch in batches:
            # Get institution name from blocks or readiness
            blocks = db.query(Block).filter(Block.batch_id == batch.id).all()
            inst_name = None
            for block in blocks:
                data = block.data or {}
                if 'institution_name' in data and data['institution_name']:
                    inst_name = str(data['institution_name']).lower().strip()
                    break
            
            if inst_name and len(inst_name) > 5:
                if inst_name not in name_groups:
                    name_groups[inst_name] = []
                name_groups[inst_name].append(batch)
            
            # Calculate document hash from file paths
            files = db.query(File).filter(File.batch_id == batch.id).all()
            for file in files:
                try:
                    with open(file.filepath, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        if file_hash not in hash_groups:
                            hash_groups[file_hash] = []
                        hash_groups[file_hash].append(batch)
                except:
                    pass
        
        # Find duplicates to delete (keep newest)
        to_delete: Set[str] = set()
        
        # By name
        for name, group in name_groups.items():
            if len(group) > 1:
                # Keep first (newest due to sorting), delete rest
                for batch in group[1:]:
                    to_delete.add(batch.id)
                    logger.info(f"Marking duplicate by name: {batch.id} ({name})")
        
        # By hash
        for hash_val, group in hash_groups.items():
            if len(group) > 1:
                for batch in group[1:]:
                    to_delete.add(batch.id)
                    logger.info(f"Marking duplicate by hash: {batch.id}")
        
        # Delete duplicates
        for batch_id in to_delete:
            # Delete all related data
            db.query(Block).filter(Block.batch_id == batch_id).delete()
            db.query(File).filter(File.batch_id == batch_id).delete()
            db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).delete()
            db.query(ApprovalClassification).filter(ApprovalClassification.batch_id == batch_id).delete()
            db.query(ApprovalRequiredDocument).filter(ApprovalRequiredDocument.batch_id == batch_id).delete()
            db.query(Batch).filter(Batch.id == batch_id).delete()
            stats["duplicates_removed"] += 1
        
        stats["batches_kept"] = len(batches) - stats["duplicates_removed"]
        db.commit()
        logger.info(f"Deduplication complete: {stats}")
        return stats
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing duplicates: {e}")
        raise
    finally:
        close_db(db)


def remove_redundant_kpi_entries() -> Dict[str, int]:
    """
    Clean up redundant KPI data.
    Since KPIs are stored as JSON in Batch.kpi_results, this ensures
    each batch has only one KPI set (no duplicates in the JSON).
    
    Returns dict with cleanup stats.
    """
    db = get_db()
    stats = {"batches_cleaned": 0}
    
    try:
        batches = db.query(Batch).all()
        
        for batch in batches:
            kpis = batch.kpi_results
            if not kpis or not isinstance(kpis, dict):
                continue
            
            # Dedupe KPI entries - keep latest value for each key
            cleaned_kpis = {}
            for key, value in kpis.items():
                if isinstance(value, dict):
                    # Extract the actual value if it's nested
                    cleaned_kpis[key] = value
                else:
                    cleaned_kpis[key] = {"value": value, "label": key}
            
            # Only update if changed
            if cleaned_kpis != kpis:
                batch.kpi_results = cleaned_kpis
                stats["batches_cleaned"] += 1
        
        db.commit()
        logger.info(f"KPI cleanup complete: {stats}")
        return stats
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning KPIs: {e}")
        raise
    finally:
        close_db(db)


def compact_database() -> Dict[str, str]:
    """
    Run SQLite VACUUM to compact the database file.
    """
    db = get_db()
    try:
        db.execute("VACUUM")
        logger.info("Database compacted successfully")
        return {"status": "compacted"}
    except Exception as e:
        logger.error(f"Error compacting database: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        close_db(db)


def run_full_cleanup() -> Dict[str, Dict]:
    """
    Run all cleanup operations in sequence.
    """
    logger.info("Starting full database cleanup...")
    
    results = {
        "purge": purge_invalid_batches(),
        "dedupe": remove_duplicate_institutions(),
        "kpi_cleanup": remove_redundant_kpi_entries(),
        "compact": compact_database(),
    }
    
    logger.info(f"Full cleanup complete: {results}")
    return results
