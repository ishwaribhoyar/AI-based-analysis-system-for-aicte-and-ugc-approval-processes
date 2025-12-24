"""
Lightweight approval classifier for AICTE / UGC / Mixed batches.
Rules are keyword based to keep deterministic behavior.
"""

from typing import Dict, List


def classify_approval(full_text: str) -> Dict[str, str]:
    """
    Classify the approval category and subtype from raw PDF text.
    
    Returns:
        {
            "category": "aicte" | "ugc" | "mixed" | "unknown",
            "subtype": "new" | "renewal" | "unknown",
            "signals": [<matched keywords>]
        }
    """
    if not full_text:
        return {"category": "unknown", "subtype": "unknown", "signals": []}
    
    text_lower = full_text.lower()
    signals: List[str] = []
    
    # Category detection
    is_aicte = "aicte application" in text_lower or "aicte" in text_lower
    is_ugc = "ugc act" in text_lower or "ugc" in text_lower
    
    if "aicte application" in text_lower:
        signals.append("aicte application")
    if "ugc act" in text_lower:
        signals.append("ugc act")
    
    # Subtype detection
    subtype = "unknown"
    if "3-year plan" in text_lower or "3 year plan" in text_lower or "3-5 year" in text_lower or "5 year plan" in text_lower:
        subtype = "new"
        signals.append("3-year plan")
    if "last academic year report" in text_lower:
        subtype = "renewal"
        signals.append("last academic year report")
    if "renewal" in text_lower and subtype == "unknown":
        subtype = "renewal"
        signals.append("renewal")
    
    if is_aicte and is_ugc:
        category = "mixed"
    elif is_aicte:
        category = "aicte"
    elif is_ugc:
        category = "ugc"
    else:
        category = "unknown"
    
    return {"category": category, "subtype": subtype, "signals": signals}

