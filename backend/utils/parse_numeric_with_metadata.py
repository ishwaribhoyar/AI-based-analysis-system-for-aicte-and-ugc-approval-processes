"""
Extended numeric parsing helper with metadata.

This module is ADDITIVE and does NOT change the behavior of the core
`parse_numeric` helper. Instead it wraps it and provides extra metadata
for consumers that need richer information (units, LPA/INR conversion,
sqm conversion, etc.).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .parse_numeric import parse_numeric


def parse_numeric_with_metadata(value: Any) -> Dict[str, Any]:
    """
    Parse a numeric string and return metadata.

    Returns a dict:
        {
          "raw": original_string,
          "value": parsed_float_or_None,   # same semantics as parse_numeric()
          "unit": detected_unit_optional,
          "is_lpa": bool_optional,
          "inr": converted_salary_optional,
          "sqm": converted_area_optional,
        }

    This helper is tolerant to non-string inputs and will attempt to
    stringify them before parsing.
    """
    metadata: Dict[str, Any] = {
        "raw": value,
        "value": None,
        "unit": None,
        "is_lpa": False,
        "inr": None,
        "sqm": None,
    }

    if value is None:
        return metadata

    if isinstance(value, (int, float)):
        metadata["value"] = float(value)
        return metadata

    if not isinstance(value, str):
        value = str(value)

    raw_str = value.strip()
    metadata["raw"] = raw_str

    if not raw_str:
        return metadata

    # Normalize some spacing for pattern checks
    text = raw_str.replace("\u00a0", " ")

    # --- Detect LPA (salary) ---
    lpa_match = re.search(r"(\d+[\d,]*\.?\d*)\s*(?:lpa|l\.p\.a\.)", text, re.IGNORECASE)
    if lpa_match:
        try:
            num_str = lpa_match.group(1).replace(",", "")
            lpa_val = float(num_str)
            metadata["value"] = lpa_val
            metadata["is_lpa"] = True
            # Convert LPA to approximate INR using lakh (1 LPA ~ 1,00,000 per year)
            metadata["inr"] = lpa_val * 100_000
            return metadata
        except (ValueError, TypeError):
            pass

    # --- Detect Indian number formats / crore / lakh ---
    # Examples: "65,00,000", "2.8 Cr", "1.25 Cr", "7.5 Lakh"

    # Crore patterns
    crore_match = re.search(r"(\d+[\d,]*\.?\d*)\s*(?:cr|crore|crores)\b", text, re.IGNORECASE)
    if crore_match:
        try:
            num_str = crore_match.group(1).replace(",", "")
            base = float(num_str)
            metadata["value"] = base * 10_000_000  # 1 Cr = 1e7
            return metadata
        except (ValueError, TypeError):
            pass

    # Lakh patterns
    lakh_match = re.search(r"(\d+[\d,]*\.?\d*)\s*(?:lakh|lakhs|lac|lacs)\b", text, re.IGNORECASE)
    if lakh_match:
        try:
            num_str = lakh_match.group(1).replace(",", "")
            base = float(num_str)
            metadata["value"] = base * 100_000  # 1 lakh = 1e5
            return metadata
        except (ValueError, TypeError):
            pass

    # Pure Indian comma format like "65,00,000" (assume rupees)
    indian_number_match = re.fullmatch(r"\d{1,3}(?:,\d{2}){1,3}", text)
    if indian_number_match:
        try:
            cleaned = text.replace(",", "")
            metadata["value"] = float(cleaned)
            return metadata
        except (ValueError, TypeError):
            pass

    # --- Area with units ---
    # Example: "185,000 sq.ft", "185000 sqft"
    area_match = re.search(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(sq\.?\s*ft|sqft|square\s*feet)",
        text,
        re.IGNORECASE,
    )
    if area_match:
        try:
            num_str = area_match.group(1).replace(",", "")
            sqft_val = float(num_str)
            metadata["value"] = sqft_val
            metadata["unit"] = "sqft"
            # Convert sqft to sqm (approx 1 sqm = 10.7639 sqft)
            metadata["sqm"] = sqft_val / 10.7639
            return metadata
        except (ValueError, TypeError):
            pass

    # --- Area with sqm units ---
    # Example: "18,500 sqm", "18500 sq.m", "18500 square meter"
    sqm_match = re.search(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(sq\.?\s*m(?:eter|etre)?s?|sqm)",
        text,
        re.IGNORECASE,
    )
    if sqm_match:
        try:
            num_str = sqm_match.group(1).replace(",", "")
            sqm_val = float(num_str)
            metadata["value"] = sqm_val
            metadata["unit"] = "sqm"
            metadata["sqm"] = sqm_val  # Already in sqm
            return metadata
        except (ValueError, TypeError):
            pass

    # Fallback: use existing parse_numeric semantics
    numeric_val: Optional[float] = parse_numeric(raw_str)
    metadata["value"] = numeric_val
    return metadata



