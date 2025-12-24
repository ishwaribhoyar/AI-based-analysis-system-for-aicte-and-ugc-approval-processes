"""
Approval Classification Service.
Classifies documents as AICTE/UGC, new/renewal based on content analysis.
ALWAYS returns a dict, never a string.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of approval classification."""
    category: str  # aicte, ugc, mixed
    subtype: str  # new, renewal, unknown
    confidence: float
    signals: List[str]


def normalize_classification(classification: Any) -> Dict[str, Any]:
    """
    Normalize classification to a dict format.
    Handles ClassificationResult dataclass, dict, string, or None.
    """
    if classification is None:
        return {
            "category": "unknown",
            "subtype": "unknown",
            "confidence": 0.0,
            "signals": []
        }
    
    if isinstance(classification, dict):
        return classification
    
    if isinstance(classification, ClassificationResult):
        return {
            "category": classification.category,
            "subtype": classification.subtype,
            "confidence": classification.confidence,
            "signals": classification.signals
        }
    
    if isinstance(classification, str):
        # Try to parse as category
        return {
            "category": classification if classification in ["aicte", "ugc", "mixed"] else "unknown",
            "subtype": "unknown",
            "confidence": 0.0,
            "signals": []
        }
    
    # Unknown type
    return {
        "category": "unknown",
        "subtype": "unknown",
        "confidence": 0.0,
        "signals": []
    }


# Keyword patterns for classification
AICTE_KEYWORDS = [
    "aicte", "all india council", "technical education",
    "nba", "national board of accreditation",
    "engineering", "pharmacy", "management", "mba", "mca",
    "polytechnic", "technical institution"
]

UGC_KEYWORDS = [
    "ugc", "university grants commission",
    "naac", "autonomous college", "deemed university",
    "affiliated college", "state university",
    "undergraduate", "postgraduate", "research"
]

NEW_APPROVAL_KEYWORDS = [
    "new institution", "new college", "new university",
    "establishment", "first time approval", "fresh approval",
    "commencement", "new courses", "starting"
]

RENEWAL_KEYWORDS = [
    "renewal", "extension", "continuation",
    "re-accreditation", "subsequent approval",
    "annual report", "previous year", "last year",
    "existing courses", "ongoing"
]


def normalize_classification(output: Any) -> Dict[str, Any]:
    """
    Normalize classification output to always return a dict.
    
    Handles:
    - Dict input → return as-is (validate structure)
    - ClassificationResult → convert to dict
    - String like "aicte-new" → parse into dict
    - String like "aicte" or "ugc" → return with subtype="unknown"
    - Anything else → return default dict
    """
    # If already a dict, validate and return
    if isinstance(output, dict):
        # Ensure required keys exist
        result = {
            "category": output.get("category", "unknown"),
            "subtype": output.get("subtype", "unknown"),
            "signals": output.get("signals", []) if isinstance(output.get("signals"), list) else [],
            "confidence": output.get("confidence", 0.0) if "confidence" in output else 0.0
        }
        # Validate category and subtype values
        if result["category"] not in ["aicte", "ugc", "mixed", "unknown"]:
            result["category"] = "unknown"
        if result["subtype"] not in ["new", "renewal", "unknown"]:
            result["subtype"] = "unknown"
        return result
    
    # If ClassificationResult dataclass, convert to dict
    if hasattr(output, 'category') and hasattr(output, 'subtype'):
        return {
            "category": getattr(output, 'category', 'unknown'),
            "subtype": getattr(output, 'subtype', 'unknown'),
            "signals": getattr(output, 'signals', []) if hasattr(output, 'signals') else [],
            "confidence": getattr(output, 'confidence', 0.0) if hasattr(output, 'confidence') else 0.0
        }
    
    # If string, try to parse
    if isinstance(output, str):
        output_lower = output.lower().strip()
        
        # Parse "aicte-new" or "ugc-renewal" format
        if "-" in output_lower:
            parts = output_lower.split("-", 1)
            category = parts[0].strip()
            subtype = parts[1].strip()
            
            if category in ["aicte", "ugc", "mixed"]:
                if subtype in ["new", "renewal"]:
                    return {
                        "category": category,
                        "subtype": subtype,
                        "signals": [f"Parsed from string: {output}"],
                        "confidence": 0.5
                    }
                else:
                    return {
                        "category": category,
                        "subtype": "unknown",
                        "signals": [f"Parsed category from string: {output}"],
                        "confidence": 0.4
                    }
        
        # Single category like "aicte" or "ugc"
        if output_lower in ["aicte", "ugc", "mixed"]:
            return {
                "category": output_lower,
                "subtype": "unknown",
                "signals": [f"Parsed category from string: {output}"],
                "confidence": 0.4
            }
    
    # Default fallback
    logger.warning(f"Could not normalize classification output: {type(output)} = {output}")
    return {
        "category": "unknown",
        "subtype": "unknown",
        "signals": [f"Unknown classification format: {type(output)}"],
        "confidence": 0.0
    }


def classify_approval(text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Classify document for approval type and subtype.
    ALWAYS returns a dict, never a string or ClassificationResult.
    
    Args:
        text: Full document text
        metadata: Optional document metadata
    
    Returns:
        Dict with category, subtype, confidence, signals
    """
    try:
        if not text:
            return {
                "category": "unknown",
                "subtype": "unknown",
                "confidence": 0.0,
                "signals": ["No text content"]
            }
        
        text_lower = text.lower()
        signals = []
        
        # Count keyword matches
        aicte_count = sum(1 for kw in AICTE_KEYWORDS if kw in text_lower)
        ugc_count = sum(1 for kw in UGC_KEYWORDS if kw in text_lower)
        new_count = sum(1 for kw in NEW_APPROVAL_KEYWORDS if kw in text_lower)
        renewal_count = sum(1 for kw in RENEWAL_KEYWORDS if kw in text_lower)
        
        # Determine category
        if aicte_count > ugc_count * 2:
            category = "aicte"
            signals.append(f"AICTE keywords: {aicte_count}")
        elif ugc_count > aicte_count * 2:
            category = "ugc"
            signals.append(f"UGC keywords: {ugc_count}")
        elif aicte_count > 0 and ugc_count > 0:
            category = "mixed"
            signals.append(f"Both AICTE ({aicte_count}) and UGC ({ugc_count}) keywords found")
        elif aicte_count > 0:
            category = "aicte"
            signals.append(f"AICTE keywords: {aicte_count}")
        elif ugc_count > 0:
            category = "ugc"
            signals.append(f"UGC keywords: {ugc_count}")
        else:
            category = "unknown"
            signals.append("No regulatory body keywords found")
        
        # Determine subtype
        if new_count > renewal_count:
            subtype = "new"
            signals.append(f"New approval signals: {new_count}")
        elif renewal_count > new_count:
            subtype = "renewal"
            signals.append(f"Renewal signals: {renewal_count}")
        else:
            # Check for year patterns suggesting existing institution
            year_pattern = r'(20[1-2][0-9][-–]20[1-2][0-9]|20[1-2][0-9][-–][0-9]{2})'
            years = re.findall(year_pattern, text)
            if len(years) >= 2:
                subtype = "renewal"
                signals.append(f"Multiple year references found: {len(years)}")
            else:
                subtype = "unknown"
                signals.append("Could not determine new/renewal")
        
        # Calculate confidence
        total_signals = aicte_count + ugc_count + new_count + renewal_count
        if total_signals >= 10:
            confidence = 0.9
        elif total_signals >= 5:
            confidence = 0.75
        elif total_signals >= 2:
            confidence = 0.6
        else:
            confidence = 0.4
        
        result = {
            "category": category,
            "subtype": subtype,
            "confidence": confidence,
            "signals": signals
        }
        
        # Normalize to ensure it's valid
        return normalize_classification(result)
        
    except Exception as e:
        logger.error(f"Error in classify_approval: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "category": "unknown",
            "subtype": "unknown",
            "confidence": 0.0,
            "signals": [f"Classification error: {str(e)}"]
        }


def get_required_documents(category: str, subtype: str) -> List[Dict[str, Any]]:
    """
    Get list of required documents based on category and subtype.
    """
    # Ensure inputs are strings
    if not isinstance(category, str):
        category = str(category) if category else "aicte"
    if not isinstance(subtype, str):
        subtype = str(subtype) if subtype else "unknown"
    
    base_docs = [
        {"name": "Institution Information", "required": True},
        {"name": "Infrastructure Details", "required": True},
        {"name": "Faculty Details", "required": True},
        {"name": "Student Enrollment", "required": True},
    ]
    
    if category == "aicte":
        base_docs.extend([
            {"name": "AICTE Approval Letter", "required": True},
            {"name": "NBA Accreditation", "required": False},
            {"name": "Technical Course Details", "required": True},
        ])
        if subtype == "renewal":
            base_docs.extend([
                {"name": "Previous Year Report", "required": True},
                {"name": "Compliance Report", "required": True},
            ])
    
    elif category == "ugc":
        base_docs.extend([
            {"name": "UGC Recognition", "required": True},
            {"name": "NAAC Accreditation", "required": False},
            {"name": "Research Output", "required": False},
        ])
        if subtype == "renewal":
            base_docs.extend([
                {"name": "Annual Quality Report", "required": True},
            ])
    
    return base_docs


def calculate_readiness_score(
    classification: Any,  # Can be dict, ClassificationResult, or string
    present_docs: List[str],  # Can be block types or document names
    extracted_data: Dict
) -> Dict[str, Any]:
    """
    Calculate approval readiness score.
    Note: present_docs can be block types (e.g., "faculty_information") 
    or document names (e.g., "Faculty Details"). Matching is flexible.
    """
    try:
        # Normalize classification to dict
        if not isinstance(classification, dict):
            classification = normalize_classification(classification)
        
        # Validate classification dict
        if not isinstance(classification, dict):
            logger.error(f"normalize_classification returned non-dict: {type(classification)}")
            classification = {"category": "unknown", "subtype": "unknown", "signals": [], "confidence": 0.0}
        
        # Get category and subtype safely
        category = classification.get("category", "unknown")
        subtype = classification.get("subtype", "unknown")
        
        if not isinstance(category, str):
            category = str(category) if category else "unknown"
        if not isinstance(subtype, str):
            subtype = str(subtype) if subtype else "unknown"
        
        # Ensure present_docs is a list of strings
        if not isinstance(present_docs, list):
            logger.warning(f"present_docs is not a list: {type(present_docs)}, converting")
            present_docs = [str(pd) for pd in (present_docs if present_docs else [])]
        else:
            # Filter and convert to strings
            present_docs = [str(pd) for pd in present_docs if pd is not None]
        
        # Ensure extracted_data is a dict
        if not isinstance(extracted_data, dict):
            logger.warning(f"extracted_data is not a dict: {type(extracted_data)}, using empty dict")
            extracted_data = {}
        
        required_docs = get_required_documents(category, subtype)
        
        # Ensure required_docs is a list of dicts
        if not isinstance(required_docs, list):
            logger.error(f"get_required_documents returned {type(required_docs)}, expected list")
            required_docs = []
        
        # Filter to only dict items
        required_docs = [d for d in required_docs if isinstance(d, dict)]
        
        # Check which required docs are present
        required_count = sum(1 for d in required_docs if d.get("required", False) is True)
        present_count = 0
        missing = []
        
        # Normalize present_docs to lowercase for matching
        present_docs_lower = [str(pd).lower() for pd in present_docs if pd]
        
        for doc in required_docs:
            # Double-check doc is a dict (should be filtered above, but be safe)
            if not isinstance(doc, dict):
                continue
            
            # Get required flag safely
            is_required = doc.get("required", False)
            if not is_required:
                continue
            
            # Get doc name safely
            doc_name = doc.get("name", "")
            if not doc_name or not isinstance(doc_name, str):
                continue
            
            doc_name_lower = doc_name.lower()
            
            # Flexible matching: check if doc name appears in present_docs or vice versa
            found = any(
                doc_name_lower in pd or pd in doc_name_lower or
                any(keyword in pd for keyword in doc_name_lower.split()) or
                any(keyword in doc_name_lower for keyword in pd.split("_"))
                for pd in present_docs_lower
            )
            
            if found:
                present_count += 1
            else:
                missing.append(doc_name)
        
        readiness = (present_count / required_count * 100) if required_count > 0 else 0
        
        # Get classification attributes safely
        result = {
            "readiness_score": round(readiness, 1),
            "required_documents": required_count,
            "present_documents": present_count,
            "missing_documents": missing,
            "classification": {
                "category": category,
                "subtype": subtype,
                "confidence": classification.get("confidence", 0.0),
                "signals": classification.get("signals", []) if isinstance(classification.get("signals"), list) else []
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in calculate_readiness_score: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return safe default
        normalized = normalize_classification(classification) if classification else {"category": "unknown", "subtype": "unknown", "signals": [], "confidence": 0.0}
        return {
            "readiness_score": 0.0,
            "required_documents": 0,
            "present_documents": 0,
            "missing_documents": [],
            "classification": {
                "category": normalized.get("category", "unknown") if isinstance(normalized, dict) else "unknown",
                "subtype": normalized.get("subtype", "unknown") if isinstance(normalized, dict) else "unknown",
                "confidence": 0.0,
                "signals": []
            }
        }
