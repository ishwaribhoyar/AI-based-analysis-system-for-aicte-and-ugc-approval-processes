"""
DEPRECATED: Document quality evaluation service
This service is kept for backward compatibility but is no longer used.
The system now uses BlockQualityService for information block quality checks.
"""

from typing import List, Dict, Any
from datetime import datetime
from models.document import DocumentQuality

class QualityService:
    def evaluate_document_quality(
        self,
        document: Dict[str, Any],
        all_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate document quality
        Returns: {
            quality_flags: List[str],
            quality_score: float,
            is_duplicate: bool,
            is_outdated: bool,
            is_low_quality: bool,
            is_invalid: bool
        }
        """
        flags = []
        is_duplicate = False
        is_outdated = False
        is_low_quality = False
        is_invalid = False
        
        # Check for duplicates
        file_hash = document.get("file_hash")
        if file_hash:
            duplicates = [d for d in all_documents 
                         if d.get("file_hash") == file_hash and d.get("document_id") != document.get("document_id")]
            if duplicates:
                is_duplicate = True
                flags.append("duplicate")
        
        # Check for outdated documents
        extracted_data = document.get("extracted_data", {})
        expiry_date = extracted_data.get("expiry_date") or extracted_data.get("expiration_date")
        if expiry_date:
            try:
                if isinstance(expiry_date, str):
                    exp_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                else:
                    exp_date = expiry_date
                
                if exp_date < datetime.utcnow():
                    is_outdated = True
                    flags.append("outdated")
            except:
                pass
        
        # Check for low quality (OCR confidence)
        classification_confidence = document.get("classification_confidence", 1.0)
        extraction_confidence = document.get("extraction_confidence", 1.0)
        
        if classification_confidence < 0.5 or extraction_confidence < 0.5:
            is_low_quality = True
            flags.append("low_quality")
        
        # Check for invalid (classification mismatch)
        doc_type = document.get("doc_type")
        if doc_type == "unknown" or classification_confidence < 0.3:
            is_invalid = True
            flags.append("invalid")
        
        # Calculate quality score
        quality_score = min(classification_confidence, extraction_confidence or 1.0)
        if is_duplicate:
            quality_score *= 0.5
        if is_outdated:
            quality_score *= 0.6
        if is_low_quality:
            quality_score *= 0.7
        if is_invalid:
            quality_score *= 0.3
        
        return {
            "quality_flags": flags,
            "quality_score": quality_score,
            "is_duplicate": is_duplicate,
            "is_outdated": is_outdated,
            "is_low_quality": is_low_quality,
            "is_invalid": is_invalid
        }

