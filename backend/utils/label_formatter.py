"""
Label formatter utility for comparison module.
Generates readable institution labels and names.
"""

import re
from typing import Optional, Dict, Any


def _year_suffix(academic_year: Optional[str], batch_id: str) -> str:
    """Return two-digit year suffix (e.g., '24')."""
    if academic_year:
        year_match = re.search(r"(\d{4})[-–]?(\d{2})?", academic_year)
        if year_match:
            return year_match.group(2) or year_match.group(1)[-2:]
    batch_year_match = re.search(r"_(\d{4})(\d{2})(\d{2})_", batch_id)
    if batch_year_match:
        return batch_year_match.group(1)[-2:]
    return "24"


def _abbrev_from_name(institution_name: Optional[str], batch_id: str) -> str:
    """Return a 3-letter abbreviation from the institution name, fallback to batch id."""
    if institution_name:
        words = [w for w in institution_name.split() if w]
        if words:
            letters = "".join(w[0].upper() for w in words[:3])
            if len(letters) >= 2:
                return letters[:3].ljust(3, letters[-1])  # ensure length 3
        # fallback to first word first 3 chars
        clean = institution_name.strip().upper()
        if len(clean) >= 3:
            return clean[:3]
    # Last resort: INS + last 2 of batch id
    return f"INS{batch_id[-2:].upper()}"


def generate_short_label(institution_name: Optional[str], batch_id: str, academic_year: Optional[str] = None) -> str:
    """
    Generate a short label like 'SIT-24' from institution name and year (3-letter abbreviation + 2-digit year).
    To ensure uniqueness, append last 2 chars of batch_id if needed.
    """
    year_suffix = _year_suffix(academic_year, batch_id)
    abbrev = _abbrev_from_name(institution_name, batch_id)
    # Add last 2 chars of batch_id to ensure uniqueness
    unique_suffix = batch_id[-2:].upper()
    return f"{abbrev}-{year_suffix}-{unique_suffix}"


def format_institution_name(institution_name: Optional[str], batch_id: str) -> str:
    """
    Get readable institution name with fallback.
    
    Args:
        institution_name: Full name from database
        batch_id: Batch ID as fallback
    
    Returns:
        Readable name like "Sunrise Institute" or "Institution #a1b2"
    """
    if institution_name and len(institution_name.strip()) > 0:
        return institution_name.strip()
    
    # Fallback: Institution #<last 4 of batch_id>
    return f"Institution #{batch_id[-4:]}"


def format_metric_name(metric_key: str) -> str:
    """
    Convert metric key to readable label.
    
    Examples:
        fsr → FSR Score
        infrastructure → Infrastructure Score
        placement_index → Placement Index
        lab_compliance_index → Lab Compliance Index
        overall → Overall Score
    """
    metric_map = {
        'fsr': 'FSR Score',
        'fsr_score': 'FSR Score',
        'infrastructure': 'Infrastructure Score',
        'infrastructure_score': 'Infrastructure Score',
        'placement_index': 'Placement Index',
        'placement': 'Placement Index',
        'lab_compliance_index': 'Lab Compliance Index',
        'lab_compliance': 'Lab Compliance',
        'overall': 'Overall Score',
        'overall_score': 'Overall Score',
        'aicte_overall_score': 'AICTE Overall',
        'ugc_overall_score': 'UGC Overall',
        'sufficiency': 'Sufficiency %',
        'compliance_flags': 'Compliance Flags',
    }
    
    if metric_key.lower() in metric_map:
        return metric_map[metric_key.lower()]
    
    # Generic formatting: replace underscores, title case
    return metric_key.replace('_', ' ').title()


def extract_academic_year_from_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract academic year from extracted block data.
    """
    # Common fields that might contain academic year
    year_fields = ['academic_year', 'year', 'session', 'academic_session']
    
    for field in year_fields:
        if field in data and data[field]:
            return str(data[field])
    
    # Look in nested data
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                result = extract_academic_year_from_data(val)
                if result:
                    return result
            elif 'year' in key.lower() and val:
                return str(val)
    
    return None
