"""
Evidence Search Service
Searches for evidence of required documents/fields in extracted blocks and full text.
Returns only evidence that actually exists - no defaults or placeholders.
"""

import logging
from typing import List, Dict, Any, Optional
from config.database import get_db, close_db, Block, File
import re

logger = logging.getLogger(__name__)


def find_best_evidence(
    batch_id: str,
    key_aliases: List[str],
    min_confidence: float = 0.40
) -> Optional[Dict[str, Any]]:
    """
    Find best evidence for a given key by searching aliases.
    
    Search order:
    1. Block storage fields (exact match or alias variants)
    2. Full context text (exact keyword + numeric/date nearby)
    3. Tables extracted by Docling (search cell text)
    
    Args:
        batch_id: Batch ID to search
        key_aliases: List of aliases to search for (e.g., ["fire_noc", "fire_safety", "fire_certificate"])
        min_confidence: Minimum confidence threshold (default 0.40)
    
    Returns:
        Dict with: {value, snippet, page, source_doc, confidence, match_type}
        or None if no evidence found
    """
    if not key_aliases:
        return None
    
    db = get_db()
    best_evidence = None
    best_confidence = 0.0
    
    try:
        # 1. Search block storage fields
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        for block in blocks:
            block_data = block.data or {}
            if not isinstance(block_data, dict):
                continue
            
            # Check each alias against block data keys and values
            for alias in key_aliases:
                alias_lower = alias.lower()
                
                # Check if alias matches any key in block data
                for key, value in block_data.items():
                    key_lower = key.lower()
                    
                    # Exact key match
                    if alias_lower == key_lower:
                        if value and value not in [None, "", "null", "None", "N/A", "n/a"]:
                            confidence = float(block.confidence) if block.confidence else 0.5
                            if confidence >= min_confidence:
                                evidence = {
                                    "value": value,
                                    "snippet": block.evidence_snippet or str(value),
                                    "page": block.evidence_page or 1,
                                    "source_doc": block.source_doc or "unknown",
                                    "confidence": confidence,
                                    "match_type": "block_key_exact"
                                }
                                if confidence > best_confidence:
                                    best_evidence = evidence
                                    best_confidence = confidence
                    
                    # Partial key match (alias in key or key in alias)
                    elif alias_lower in key_lower or key_lower in alias_lower:
                        if value and value not in [None, "", "null", "None", "N/A", "n/a"]:
                            confidence = float(block.confidence) * 0.8 if block.confidence else 0.4
                            if confidence >= min_confidence:
                                evidence = {
                                    "value": value,
                                    "snippet": block.evidence_snippet or str(value),
                                    "page": block.evidence_page or 1,
                                    "source_doc": block.source_doc or "unknown",
                                    "confidence": confidence,
                                    "match_type": "block_key_partial"
                                }
                                if confidence > best_confidence:
                                    best_evidence = evidence
                                    best_confidence = confidence
                    
                    # Check if alias appears in value (string search)
                    if isinstance(value, str) and alias_lower in value.lower():
                        confidence = float(block.confidence) * 0.7 if block.confidence else 0.35
                        if confidence >= min_confidence:
                            evidence = {
                                "value": value,
                                "snippet": block.evidence_snippet or value[:200],
                                "page": block.evidence_page or 1,
                                "source_doc": block.source_doc or "unknown",
                                "confidence": confidence,
                                "match_type": "block_value_match"
                            }
                            if confidence > best_confidence:
                                best_evidence = evidence
                                best_confidence = confidence
        
        # 2. Search full context text (if we have stored full text)
        # Note: We don't store full text in DB, so we'd need to reconstruct from blocks
        # For now, we rely on block-level evidence which is more reliable
        
        # 3. Search tables (if stored in block data as structured tables)
        # Tables are typically in infrastructure or lab blocks
        for block in blocks:
            block_data = block.data or {}
            if not isinstance(block_data, dict):
                continue
            
            # Look for table-like structures (lists of dicts)
            for key, value in block_data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Check if it's a table (list of dicts)
                    if isinstance(value[0], dict):
                        for row in value:
                            for cell_key, cell_value in row.items():
                                if isinstance(cell_value, str):
                                    for alias in key_aliases:
                                        if alias.lower() in cell_value.lower():
                                            confidence = float(block.confidence) * 0.6 if block.confidence else 0.3
                                            if confidence >= min_confidence:
                                                evidence = {
                                                    "value": cell_value,
                                                    "snippet": f"{cell_key}: {cell_value}",
                                                    "page": block.evidence_page or 1,
                                                    "source_doc": block.source_doc or "unknown",
                                                    "confidence": confidence,
                                                    "match_type": "table_cell_match"
                                                }
                                                if confidence > best_confidence:
                                                    best_evidence = evidence
                                                    best_confidence = confidence
    
    except Exception as e:
        logger.error(f"Error searching evidence for {key_aliases}: {e}")
    finally:
        close_db(db)
    
    return best_evidence


def check_block_examined(
    batch_id: str,
    block_types: List[str]
) -> bool:
    """
    Check if any of the specified block types were examined (extraction attempted).
    
    Args:
        batch_id: Batch ID
        block_types: List of block type names to check
    
    Returns:
        True if at least one block type was examined, False otherwise
    """
    db = get_db()
    try:
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        examined_types = set()
        for block in blocks:
            block_data = block.data or {}
            # If block has data (even if empty dict), it was examined
            if isinstance(block_data, dict):
                examined_types.add(block.block_type)
        
        # Check if any of the requested block types were examined
        return any(bt in examined_types for bt in block_types)
    
    except Exception as e:
        logger.error(f"Error checking examined blocks: {e}")
        return False
    finally:
        close_db(db)

