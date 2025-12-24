"""
Year parsing utility
Handles year ranges and formats: "2023-24" → 2024, "AY 2023/24" → 2024
"""

import re
from typing import Optional

def parse_year(value: Optional[str]) -> Optional[int]:
    """
    Parse year from various formats and normalize to integer.
    
    Handles:
    - "2023" → 2023
    - "2024" → 2024
    - "2023-24" → 2024 (later year)
    - "2023–24" → 2024 (en dash)
    - "AY 2023/24" → 2024
    - "2024/25" → 2025
    
    Returns int year (1900-2100) or None if unparsable.
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        # Try to convert if numeric
        try:
            year = int(value)
            if 1900 <= year <= 2100:
                return year
        except (ValueError, TypeError):
            pass
        return None
    
    cleaned = value.strip()
    if not cleaned:
        return None
    
    # Pattern 1: Year range "2023-24" or "2023–24" (en dash) → 2024
    range_match = re.search(r'(\d{4})\s*[-–]\s*(\d{2})', cleaned)
    if range_match:
        try:
            start_year = int(range_match.group(1))
            end_short = int(range_match.group(2))
            # Convert short year to full year
            if end_short < 50:
                end_year = 2000 + end_short
            else:
                end_year = 1900 + end_short
            # Return the later year
            return max(start_year, end_year)
        except (ValueError, AttributeError):
            pass
    
    # Pattern 2: Academic year "AY 2023/24" or "2023/24" → 2024
    ay_match = re.search(r'(?:AY|Academic\s+Year)?\s*(\d{4})\s*/\s*(\d{2})', cleaned, re.IGNORECASE)
    if ay_match:
        try:
            start_year = int(ay_match.group(1))
            end_short = int(ay_match.group(2))
            if end_short < 50:
                end_year = 2000 + end_short
            else:
                end_year = 1900 + end_short
            return max(start_year, end_year)
        except (ValueError, AttributeError):
            pass
    
    # Pattern 3: Simple 4-digit year "2023" or "2024"
    year_match = re.search(r'\b(19|20)\d{2}\b', cleaned)
    if year_match:
        try:
            year = int(year_match.group(0))
            if 1900 <= year <= 2100:
                return year
        except (ValueError, AttributeError):
            pass
    
    # Pattern 4: 2-digit year (assume 2000s if < 50, else 1900s)
    short_year_match = re.search(r'\b(\d{2})\b', cleaned)
    if short_year_match:
        try:
            short_year = int(short_year_match.group(1))
            if short_year < 50:
                year = 2000 + short_year
            else:
                year = 1900 + short_year
            if 1900 <= year <= 2100:
                return year
        except (ValueError, AttributeError):
            pass
    
    return None

