"""
Numeric parsing utility
Extracts numeric values from messy strings with currency, units, and special characters
Handles: ₹, commas, LPA/Lakhs, percentages, area units
"""

import re
from typing import Optional, Union

def parse_numeric(value: Union[str, int, float, None]) -> Optional[float]:
    """
    Extract numeric value from messy string.
    
    Handles:
    - Currency symbols: ₹, Rs., INR
    - Commas: "85,000" → 85000
    - LPA/Lakh: "4.2 LPA" → 4.2 (or 420000 if convert_lpa=True)
    - Percentages: "84.7%" → 84.7
    - Area units: "18,500 sq. m" → 18500
    - Lakh/Crore: "1.2 lakh" → 120000, "5 Cr" → 50000000
    
    Returns float/int or None if unparsable.
    """
    if value is None:
        return None
    
    # If already numeric, return as float
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return None
    
    # Clean the string
    cleaned = value.strip()
    if not cleaned:
        return None
    
    # Pattern 1: Percentage "84.7%" → 84.7
    percent_match = re.search(r'(\d+\.?\d*)\s*%', cleaned, re.IGNORECASE)
    if percent_match:
        try:
            return float(percent_match.group(1))
        except (ValueError, AttributeError):
            pass
    
    # Pattern 2: LPA "4.2 LPA" → 4.2 (LPA value; caller may convert to INR)
    lpa_match = re.search(r'(\d+\.?\d*)\s*(?:LPA|lpa|L\.P\.A\.)', cleaned, re.IGNORECASE)
    if lpa_match:
        try:
            return float(lpa_match.group(1))
        except (ValueError, AttributeError):
            pass
    
    # Pattern 3: Lakh "X lakh" → X * 100000
    lakh_match = re.search(r'(\d+\.?\d*)\s*(?:lakh|lakhs|L|Lakh|Lakhs)', cleaned, re.IGNORECASE)
    if lakh_match:
        try:
            num = float(lakh_match.group(1))
            return num * 100000
        except (ValueError, AttributeError):
            pass
    
    # Pattern 4: Crore "X crore" → X * 10000000
    crore_match = re.search(r'(\d+\.?\d*)\s*(?:crore|crores|Cr|Crore|Crores)', cleaned, re.IGNORECASE)
    if crore_match:
        try:
            num = float(crore_match.group(1))
            return num * 10000000
        except (ValueError, AttributeError):
            pass
    
    # Pattern 5: Currency symbols (₹, Rs., INR) followed by number
    currency_patterns = [
        r'[₹]\s*(\d+[,\d]*\.?\d*)',  # ₹85,000
        r'Rs\.?\s*(\d+[,\d]*\.?\d*)',  # Rs. 85000 or Rs 85000
        r'INR\s*(\d+[,\d]*\.?\d*)',  # INR 85000
    ]
    for pattern in currency_patterns:
        currency_match = re.search(pattern, cleaned, re.IGNORECASE)
        if currency_match:
            try:
                num_str = currency_match.group(1).replace(',', '')
                return float(num_str)
            except (ValueError, AttributeError):
                pass
    
    # Pattern 6: Area units with conversion
    # Square meters: "18,500 sq. m" or "18500 sqm" → 18500
    area_sqm_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s*(?:meter|metre|m))', cleaned, re.IGNORECASE)
    if area_sqm_match:
        try:
            num_str = area_sqm_match.group(1).replace(',', '')
            return float(num_str)
        except (ValueError, AttributeError):
            pass
    
    # Square feet: "18,500 sq. ft" or "18500 sqft" → convert to sqm (multiply by 0.092903)
    area_sqft_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft|square\s*(?:feet|ft))', cleaned, re.IGNORECASE)
    if area_sqft_match:
        try:
            num_str = area_sqft_match.group(1).replace(',', '')
            sqft_value = float(num_str)
            # Convert sqft to sqm: 1 sqft = 0.092903 sqm
            return sqft_value * 0.092903
        except (ValueError, AttributeError):
            pass
    
    # Acres: "5 acres" or "5 ac" → convert to sqm (multiply by 4046.86)
    acres_match = re.search(r'(\d+\.?\d*)\s*(?:acre|acres|ac\.?)', cleaned, re.IGNORECASE)
    if acres_match:
        try:
            num_str = acres_match.group(1).replace(',', '')
            acres_value = float(num_str)
            # Convert acres to sqm: 1 acre = 4046.86 sqm
            return acres_value * 4046.86
        except (ValueError, AttributeError):
            pass
    
    # Hectares: "2 hectares" or "2 ha" → convert to sqm (multiply by 10000)
    hectares_match = re.search(r'(\d+\.?\d*)\s*(?:hectare|hectares|ha\.?)', cleaned, re.IGNORECASE)
    if hectares_match:
        try:
            num_str = hectares_match.group(1).replace(',', '')
            hectares_value = float(num_str)
            # Convert hectares to sqm: 1 hectare = 10000 sqm
            return hectares_value * 10000
        except (ValueError, AttributeError):
            pass
    
    # Pattern 7: Extract first number (with decimals, commas)
    # Remove common words: students, FTE, sqm, sq ft, etc.
    cleaned_for_number = re.sub(
        r'\b(students|student|FTE|fte|sq\.?\s*ft|square\s*(?:feet|ft)|area|count|number|total|per|each)\b',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    
    # Find first number (with optional decimals and commas)
    number_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', cleaned_for_number)
    if number_match:
        try:
            num_str = number_match.group(1).replace(',', '')
            return float(num_str)
        except (ValueError, AttributeError):
            pass
    
    # Pattern 8: Simple number extraction (last resort)
    numbers = re.findall(r'\d+\.?\d*', cleaned)
    if numbers:
        try:
            return float(numbers[0])
        except (ValueError, IndexError):
            pass
    
    return None


def parse_numeric_with_metadata(value) -> dict:
    """
    Parse numeric value with metadata about the parsing.
    
    Returns:
    {
        "value": float or None,
        "raw": original string,
        "unit": detected unit,
        "parse_success": bool,
        "format_detected": str
    }
    """
    result = {
        "value": None,
        "raw": str(value) if value is not None else None,
        "unit": None,
        "parse_success": False,
        "format_detected": "unknown"
    }
    
    if value is None:
        result["format_detected"] = "null"
        return result
    
    if isinstance(value, (int, float)):
        result["value"] = float(value)
        result["parse_success"] = True
        result["format_detected"] = "numeric"
        return result
    
    if not isinstance(value, str):
        return result
    
    clean = value.strip().lower()
    
    # Detect format
    if "%" in clean:
        result["unit"] = "%"
        result["format_detected"] = "percentage"
    elif "lpa" in clean:
        result["unit"] = "lpa"
        result["format_detected"] = "lpa"
    elif "crore" in clean or "cr" in clean:
        result["unit"] = "cr"
        result["format_detected"] = "crore"
    elif "lakh" in clean:
        result["unit"] = "lakhs"
        result["format_detected"] = "lakhs"
    elif any(x in clean for x in ["sq.ft", "sqft", "sq ft"]):
        result["unit"] = "sqft"
        result["format_detected"] = "sqft"
    elif any(x in clean for x in ["sq.m", "sqm", "sq m"]):
        result["unit"] = "sqm"
        result["format_detected"] = "sqm"
    elif any(x in clean for x in ["acre", "acres", "ac."]):
        result["unit"] = "acres"
        result["format_detected"] = "acres"
    elif any(x in clean for x in ["hectare", "hectares", "ha."]):
        result["unit"] = "hectares"
        result["format_detected"] = "hectares"
    
    # Use existing parse_numeric for actual parsing (includes unit conversion)
    parsed = parse_numeric(value)
    if parsed is not None:
        result["value"] = parsed
        result["parse_success"] = True
        # If unit was sqft/acres/hectares, value is already converted to sqm
        if result["unit"] in ["sqft", "acres", "hectares"]:
            result["unit"] = "sqm"  # Value is now in sqm after conversion
    
    return result


def sqft_to_sqm(sqft: float) -> float:
    """Convert square feet to square meters."""
    return sqft * 0.092903


def ensure_area_in_sqm(value: Union[str, int, float, None], field_name: str = "") -> Optional[float]:
    """
    Ensure area value is in square meters.
    Handles conversion from sqft, acres, hectares to sqm.
    Returns None if value cannot be parsed.
    """
    if value is None:
        return None
    
    # If already numeric, assume it's in sqm (or use field name hint)
    if isinstance(value, (int, float)):
        # If field name suggests sqft, convert
        if field_name and "sqft" in field_name.lower():
            return sqft_to_sqm(float(value))
        return float(value)
    
    # Parse with unit detection and conversion
    parsed = parse_numeric(value)
    return parsed  # parse_numeric already handles unit conversion


# Field aliases for canonical mapping
FIELD_ALIASES = {
    "total_faculty": ["faculty_count", "teaching_staff", "no_of_faculty", "faculty_strength"],
    "total_students": ["student_count", "total_enrollment", "enrolled_students", "student_strength"],
    "ug_enrollment": ["ug_students", "undergraduate_enrollment", "ug_intake"],
    "pg_enrollment": ["pg_students", "postgraduate_enrollment", "pg_intake"],
    "placed_students": ["students_placed", "placements", "placed_count"],
    "eligible_students": ["students_eligible", "eligible_for_placement"],
    "placement_rate": ["placement_percentage", "placement_ratio"],
    "highest_package": ["max_package", "highest_salary", "max_salary_lpa"],
    "average_package": ["avg_package", "average_salary", "mean_salary_lpa"],
    "built_up_area": ["total_built_up_area", "building_area", "campus_area"],
    "classrooms": ["classroom_count", "number_of_classrooms"],
    "library_area": ["library_size", "library_space"],
    "lab_area": ["laboratory_area", "lab_space", "total_lab_area"],
}


def find_canonical_field(data: dict, canonical_name: str):
    """Find a field value using canonical name and aliases."""
    if canonical_name in data and data[canonical_name] is not None:
        return data[canonical_name]
    
    aliases = FIELD_ALIASES.get(canonical_name, [])
    for alias in aliases:
        if alias in data and data[alias] is not None:
            return data[alias]
        if f"{alias}_num" in data and data[f"{alias}_num"] is not None:
            return data[f"{alias}_num"]
    
    return None


def apply_canonical_mapping(raw_data: dict) -> dict:
    """Apply canonical field mapping to raw extracted data."""
    canonical = {}
    
    for canonical_name in FIELD_ALIASES.keys():
        value = find_canonical_field(raw_data, canonical_name)
        if value is not None:
            parsed = parse_numeric_with_metadata(value)
            canonical[canonical_name] = value
            if parsed["value"] is not None:
                canonical[f"{canonical_name}_num"] = parsed["value"]
    
    # Derived: total_students = ug + pg if missing
    if "total_students_num" not in canonical:
        ug = canonical.get("ug_enrollment_num", 0) or 0
        pg = canonical.get("pg_enrollment_num", 0) or 0
        if ug + pg > 0:
            canonical["total_students_num"] = ug + pg
    
    # Derived: placement_rate = placed / eligible * 100
    if "placement_rate_num" not in canonical:
        placed = canonical.get("placed_students_num")
        eligible = canonical.get("eligible_students_num")
        if placed and eligible and eligible > 0:
            canonical["placement_rate_num"] = (placed / eligible) * 100
    
    return {"raw_fields": raw_data, "canonical_fields": canonical}
