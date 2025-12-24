"""
Evidence-Driven Approval Requirements Service.
Checks for required documents based on actual extracted evidence.
NO hardcoded/default outputs - all data derived from evidence.
"""

from typing import Dict, List, Any, Optional
from config.database import get_db, close_db, Block, Batch
from services.evidence_search import find_best_evidence, check_block_examined
from services.approval_classifier import normalize_classification
import logging

logger = logging.getLogger(__name__)


# Required documents by approval type
# Each key maps to aliases that could appear in extracted blocks
REQUIRED_DOCUMENTS = {
    "aicte_new": {
        "institution_info": {
            "aliases": ["institution_name", "institute_name", "college_name", "university_name"],
            "block_types": ["institution_info", "basic_info"],
            "description": "Institution Information"
        },
        "faculty_details": {
            "aliases": ["faculty_count", "teaching_staff", "total_faculty"],
            "block_types": ["faculty", "staff"],
            "description": "Faculty Details"
        },
        "infrastructure": {
            "aliases": ["built_up_area", "total_area", "land_area", "building_area"],
            "block_types": ["infrastructure", "facilities"],
            "description": "Infrastructure Details"
        },
        "lab_equipment": {
            "aliases": ["lab_area", "laboratory", "equipment", "lab_count"],
            "block_types": ["lab", "equipment"],
            "description": "Laboratory & Equipment"
        },
        "fire_noc": {
            "aliases": ["fire_noc", "fire_safety", "fire_certificate"],
            "block_types": ["safety", "compliance", "certificates"],
            "description": "Fire Safety NOC"
        },
        "aicte_approval": {
            "aliases": ["aicte_approval", "aicte_letter", "aicte_id"],
            "block_types": ["approval", "recognition"],
            "description": "AICTE Approval Letter"
        },
    },
    "aicte_renewal": {
        "institution_info": {
            "aliases": ["institution_name", "institute_name"],
            "block_types": ["institution_info", "basic_info"],
            "description": "Institution Information"
        },
        "faculty_details": {
            "aliases": ["faculty_count", "teaching_staff", "fsr"],
            "block_types": ["faculty", "staff"],
            "description": "Faculty Details"
        },
        "student_enrollment": {
            "aliases": ["total_students", "enrolled_students", "student_count"],
            "block_types": ["students", "enrollment"],
            "description": "Student Enrollment"
        },
        "placement_record": {
            "aliases": ["placement_rate", "placed_students", "placement_percentage"],
            "block_types": ["placement", "career"],
            "description": "Placement Records"
        },
        "compliance_report": {
            "aliases": ["compliance", "norms", "deficiency"],
            "block_types": ["compliance", "audit"],
            "description": "Compliance Report"
        },
    },
    "ugc_new": {
        "institution_info": {
            "aliases": ["institution_name", "university_name"],
            "block_types": ["institution_info", "basic_info"],
            "description": "Institution Information"
        },
        "faculty_qualifications": {
            "aliases": ["faculty_phd", "qualified_faculty", "phd_count"],
            "block_types": ["faculty", "qualifications"],
            "description": "Faculty Qualifications"
        },
        "research_output": {
            "aliases": ["research", "publications", "patents", "papers"],
            "block_types": ["research", "publications"],
            "description": "Research Output"
        },
        "ugc_recognition": {
            "aliases": ["ugc_recognition", "ugc_approval", "12b", "2f"],
            "block_types": ["recognition", "approval"],
            "description": "UGC Recognition"
        },
    },
    "ugc_renewal": {
        "institution_info": {
            "aliases": ["institution_name", "university_name"],
            "block_types": ["institution_info", "basic_info"],
            "description": "Institution Information"
        },
        "naac_grade": {
            "aliases": ["naac", "naac_grade", "accreditation_grade"],
            "block_types": ["accreditation", "naac"],
            "description": "NAAC Accreditation"
        },
        "annual_report": {
            "aliases": ["annual_report", "year_report", "aqar"],
            "block_types": ["report", "annual"],
            "description": "Annual Quality Report"
        },
    },
}


# Use evidence_search service instead of local implementation


def check_approval_requirements(batch_id: str, approval_type: str = None) -> Dict[str, Any]:
    """
    Check which required documents are present/missing/unknown based on evidence.
    
    Args:
        batch_id: The batch to check
        approval_type: One of aicte_new, aicte_renewal, ugc_new, ugc_renewal
                      If None, auto-detect from batch
    
    Returns:
        {
            "approval_type": str,
            "present_documents": [{key, description, evidence}],
            "missing_documents": [{key, description, reason, examined}],
            "unknown_documents": [{key, description, reason}],
            "readiness_score": float
        }
    """
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return {
                "error": "Batch not found",
                "present_documents": [],
                "missing_documents": [],
                "unknown_documents": [],
                "readiness_score": 0
            }
        
        # Auto-detect approval type if not provided
        if not approval_type:
            classification = batch.approval_classification
            
            # Normalize classification to ensure it's a dict
            if not isinstance(classification, dict):
                classification = normalize_classification(classification)
            
            # Ensure classification is a dict after normalization
            if not isinstance(classification, dict):
                logger.warning(f"⚠️  Classification normalization failed, using batch mode")
                category = batch.mode or "aicte"
                subtype = "renewal"
            else:
                category = classification.get("category", batch.mode or "aicte")
                subtype = classification.get("subtype", "renewal")
            
            # Ensure category and subtype are valid
            if category not in ["aicte", "ugc", "mixed", "unknown"]:
                category = batch.mode or "aicte"
            if subtype not in ["new", "renewal", "unknown"]:
                subtype = "renewal"  # Default to renewal for existing institutions
            
            approval_type = f"{category}_{subtype}"
        
        # Get required docs for this approval type
        required = REQUIRED_DOCUMENTS.get(approval_type, REQUIRED_DOCUMENTS.get("aicte_renewal", {}))
        
        present_documents = []
        missing_documents = []
        unknown_documents = []
        
        for key, config in required.items():
            aliases = config["aliases"]
            block_types = config["block_types"]
            description = config["description"]
            
            # Check if extraction was attempted for these block types
            examined = check_block_examined(batch_id, block_types)
            
            # Find evidence using evidence_search service
            evidence = find_best_evidence(batch_id, aliases, min_confidence=0.40)
            
            if evidence and evidence.get("confidence", 0) >= 0.40:
                # Document is present with sufficient confidence
                present_documents.append({
                    "key": key,
                    "description": description,
                    "evidence": {
                        "value": evidence.get("value"),
                        "snippet": evidence.get("snippet", ""),
                        "page": evidence.get("page"),
                        "source_doc": evidence.get("source_doc"),
                        "confidence": evidence.get("confidence", 0),
                        "match_type": evidence.get("match_type"),
                    }
                })
            elif examined:
                # Extraction attempted but not found
                missing_documents.append({
                    "key": key,
                    "description": description,
                    "reason": "Not found in extracted data",
                    "examined": True
                })
            else:
                # Block type never extracted - unknown
                unknown_documents.append({
                    "key": key,
                    "description": description,
                    "reason": "No relevant block found in uploaded documents"
                })
        
        # Calculate readiness score
        total = len(required)
        present = len(present_documents)
        readiness_score = (present / total * 100) if total > 0 else 0
        
        return {
            "approval_type": approval_type,
            "present_documents": present_documents,
            "missing_documents": missing_documents,
            "unknown_documents": unknown_documents,
            "readiness_score": round(readiness_score, 1),
            "total_required": total,
            "total_present": present,
            "total_missing": len(missing_documents),
            "total_unknown": len(unknown_documents)
        }
        
    finally:
        close_db(db)
