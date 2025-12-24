"""
Approval API Router.
Provides classification and readiness scoring for approval requests.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from config.database import get_db, close_db, Batch, Block
from services.approval_classifier import (
    classify_approval,
    get_required_documents,
    calculate_readiness_score,
    normalize_classification
)

router = APIRouter()


@router.get("/approval/{batch_id}")
def get_approval_classification(batch_id: str) -> Dict[str, Any]:
    """
    Get approval classification and readiness for a batch.
    
    Returns:
    - classification: category (aicte/ugc/mixed), subtype (new/renewal)
    - required_documents: list of required docs for this subtype
    - readiness_score: percentage of requirements met
    - missing_documents: list of missing required docs
    """
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        # Combine all block text for classification
        all_text = ""
        present_docs = []
        extracted_data = {}
        
        for block in blocks:
            if block.evidence_snippet:
                all_text += " " + block.evidence_snippet
            if block.block_type:
                present_docs.append(block.block_type)
            if block.data:
                extracted_data.update(block.data or {})
        
        # Classify - returns dict or ClassificationResult
        classification_raw = classify_approval(all_text)
        classification = normalize_classification(classification_raw)
        
        # Ensure classification is a dict
        if not isinstance(classification, dict):
            classification = {
                "category": batch.mode or "aicte",
                "subtype": "unknown",
                "confidence": 0.0,
                "signals": []
            }
        
        # Get required docs
        category = classification.get("category", batch.mode or "aicte")
        subtype = classification.get("subtype", "unknown")
        required_docs = get_required_documents(category, subtype)
        
        # Calculate readiness
        readiness = calculate_readiness_score(
            classification,
            present_docs,
            extracted_data
        )
        
        return {
            "batch_id": batch_id,
            "mode": batch.mode,
            **readiness,
            "required_documents_list": required_docs
        }
    
    finally:
        close_db(db)


@router.get("/approval/{batch_id}/requirements")
def get_approval_requirements(batch_id: str) -> Dict[str, Any]:
    """
    Get detailed requirements for a batch based on classification.
    """
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        # Get text for classification
        all_text = " ".join(
            block.evidence_snippet or "" 
            for block in blocks
        )
        
        classification_raw = classify_approval(all_text)
        classification = normalize_classification(classification_raw)
        
        # Ensure classification is a dict
        if not isinstance(classification, dict):
            classification = {
                "category": batch.mode or "aicte",
                "subtype": "unknown",
                "confidence": 0.0,
                "signals": []
            }
        
        category = classification.get("category", batch.mode or "aicte")
        subtype = classification.get("subtype", "unknown")
        required_docs = get_required_documents(category, subtype)
        
        # Ensure required_docs is a list
        if not isinstance(required_docs, list):
            required_docs = []
        
        return {
            "batch_id": batch_id,
            "category": category,
            "subtype": subtype,
            "required_documents": required_docs,
            "total_required": sum(1 for d in required_docs if isinstance(d, dict) and d.get("required", False)),
            "total_optional": sum(1 for d in required_docs if isinstance(d, dict) and not d.get("required", False))
        }
    
    finally:
        close_db(db)
