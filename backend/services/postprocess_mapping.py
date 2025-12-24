"""
Post-processing helpers for AICTE blocks.

These functions run AFTER one-shot LLM extraction and initial numeric/year
parsing, and BEFORE KPIs / quality. They are additive and only fill in
missing numeric aggregates or normalized variants when safe.
"""

from __future__ import annotations

from typing import Any, Dict
import re

from utils.parse_numeric import parse_numeric
from utils.parse_numeric_with_metadata import parse_numeric_with_metadata


def _get_first_numeric(block: Dict[str, Any], keys: list[str]) -> float | None:
    """Helper to pull a numeric value from the first matching key (or its _num)."""
    for key in keys:
        if f"{key}_num" in block:
            val = block.get(f"{key}_num")
            if isinstance(val, (int, float)):
                return float(val)
        if key in block and block.get(key) not in (None, ""):
            parsed = parse_numeric(block.get(key))
            if parsed is not None:
                return parsed
    return None


def normalize_student_block(block: Dict[str, Any]) -> None:
    """
    Normalize student_enrollment_information block.

    - Auto-fill total_students_num from total_students if present
    - If total_students_num is missing but UG / PG enrollment present,
      set total_students_num = ug_enrollment_num + pg_enrollment_num.
    """
    if block is None or not isinstance(block, dict):
        return

    # Auto-fill total_students_num from total_students if present
    if "total_students" in block and block.get("total_students"):
        if "total_students_num" not in block or block.get("total_students_num") is None:
            parsed = parse_numeric(block["total_students"])
            if parsed is not None:
                block["total_students_num"] = parsed

    # If already present, do not override.
    if "total_students_num" in block and isinstance(block.get("total_students_num"), (int, float)):
        return

    # Look for UG / PG enrollment style keys - extended with more aliases
    ug_keys = [
        "ug_enrollment", "ug_enrollment_num",
        "ug_students", "ug_student",
        "ug_intake", "intake_capacity_ug", "intake_capacity_ug_num",
        "UG Enrollment", "Undergraduate Enrollment", "undergraduate enrollment",
        "Intake Capacity (UG)", "UG Intake", "UG intake",
        "total enrollment ug", "total_enrollment_ug"
    ]
    pg_keys = [
        "pg_enrollment", "pg_enrollment_num",
        "pg_students", "pg_student",
        "pg_intake", "intake_capacity_pg", "intake_capacity_pg_num",
        "PG Enrollment", "Postgraduate Enrollment", "postgraduate enrollment",
        "Intake Capacity (PG)", "PG Intake", "PG intake",
        "total enrollment pg", "total_enrollment_pg"
    ]
    
    # Also check for total_students aliases
    total_students_keys = [
        "total_students", "total_students_num",
        "total enrollment", "total_enrollment",
        "headcount", "student_count", "student_count_num",
        "total students", "total_student_count"
    ]

    ug_val = _get_first_numeric(block, ug_keys)
    pg_val = _get_first_numeric(block, pg_keys)
    
    # Check if total_students already exists
    total_students_val = _get_first_numeric(block, total_students_keys)

    if ug_val is not None:
        block.setdefault("ug_enrollment_num", ug_val)
    if pg_val is not None:
        block.setdefault("pg_enrollment_num", pg_val)
    
    # Set total_students_num: prefer existing value, else compute from UG+PG
    if total_students_val is not None:
        block.setdefault("total_students_num", total_students_val)
    elif ug_val is not None and pg_val is not None:
        total = ug_val + pg_val
        block["total_students_num"] = total
    elif total_students_val is None and (ug_val is not None or pg_val is not None):
        # If we have partial data, try to infer total if only one is present
        # (conservative: don't set total if only partial data)
        pass


def normalize_infrastructure_block(block: Dict[str, Any]) -> None:
    """
    Normalize infrastructure_information block.

    - Auto-fill built_up_area_num from built_up_area or built_up_area_raw if present
    - If built-up area appears to be in sq.ft, compute sqm and store in
      built_up_area_sqm_num while leaving original fields intact.
    """
    if block is None or not isinstance(block, dict):
        return

    # Do not override if already normalized.
    if "built_up_area_sqm_num" in block and isinstance(block.get("built_up_area_sqm_num"), (int, float)):
        return

    # Priority order: built_up_area_raw, built_up_area, then other keys
    candidate_keys = [
        "built_up_area_raw",  # Check raw first (most likely to have units)
        "built_up_area",
        "built_up_area_sqm",
        "total_area", "total area",
        "campus_area", "campus area",
        "area", "Area",
        "built up area", "Built-up Area",
        "total built area", "Total Built Area"
    ]

    for key in candidate_keys:
        raw_val = block.get(key)
        if not raw_val:
            continue
        meta = parse_numeric_with_metadata(str(raw_val))
        # Prefer sqm conversion when available.
        sqm = meta.get("sqm")
        if isinstance(sqm, (int, float)) and sqm > 0:
            block["built_up_area_sqm_num"] = float(sqm)
            # Also keep a generic numeric variant for backward uses if absent.
            if "built_up_area_num" not in block:
                val = meta.get("value")
                if isinstance(val, (int, float)):
                    block["built_up_area_num"] = float(val)
            # Ensure raw is preserved
            if "built_up_area_raw" not in block and isinstance(raw_val, str):
                block["built_up_area_raw"] = raw_val
            return

    # Fallback: if we have a numeric built_up_area already, treat it as sqm.
    if "built_up_area_num" in block and isinstance(block.get("built_up_area_num"), (int, float)):
        block["built_up_area_sqm_num"] = float(block["built_up_area_num"])


def normalize_placement_block(block: Dict[str, Any]) -> None:
    """
    Normalize placement_information block.

    - If placement_rate_num missing but eligible & placed counts present,
      compute placement_rate_num = (placed / eligible) * 100.
    """
    if block is None or not isinstance(block, dict):
        return

    if isinstance(block.get("placement_rate_num"), (int, float)):
        return

    eligible_keys = [
        "eligible_students", "eligible_students_num",
        "students_eligible", "students eligible",
        "Total Students Eligible", "total students eligible",
        "eligible", "total eligible"
    ]
    placed_keys = [
        "students_placed", "students_placed_num",
        "Total Students Placed", "total students placed",
        "placed_students", "placed students",
        "placed", "total placed"
    ]
    
    eligible = _get_first_numeric(block, eligible_keys)
    placed = _get_first_numeric(block, placed_keys)

    if eligible is None or placed is None or eligible == 0:
        return

    rate = (placed / eligible) * 100.0
    block.setdefault("eligible_students_num", eligible)
    block.setdefault("students_placed_num", placed)
    block["placement_rate_num"] = rate
    
    # Also check for placement_rate_raw and parse it if present
    placement_rate_raw = block.get("placement_rate_raw") or block.get("placement_rate")
    if placement_rate_raw and isinstance(placement_rate_raw, str):
        from utils.parse_numeric import parse_numeric
        parsed_rate = parse_numeric(placement_rate_raw)
        if parsed_rate is not None:
            # Prefer computed rate if both exist, but ensure _num variant exists
            if "placement_rate_num" not in block:
                block["placement_rate_num"] = parsed_rate


def backfill_missing_year(block: Dict[str, Any]) -> None:
    """
    Backfill missing year from academic_year_start if available.
    Prevents unwanted "outdated" flags.
    """
    if not isinstance(block, dict):
        return
    
    # If last_updated_year or parsed_year already exists, don't override
    if block.get("last_updated_year") or block.get("parsed_year"):
        return
    
    # Try to get year from academic_year_start
    academic_year_start = block.get("academic_year_start")
    if academic_year_start:
        from utils.parse_year import parse_year
        parsed = parse_year(str(academic_year_start))
        if parsed:
            block["last_updated_year"] = parsed
            block["parsed_year"] = parsed
            return
    
    # Try academic_year_end as fallback
    academic_year_end = block.get("academic_year_end")
    if academic_year_end:
        from utils.parse_year import parse_year
        parsed = parse_year(str(academic_year_end))
        if parsed:
            block["last_updated_year"] = parsed
            block["parsed_year"] = parsed
            return
    
    # Try academic_year field (format: "2023-24" or "2023-2024")
    academic_year = block.get("academic_year")
    if academic_year:
        from utils.parse_year import parse_year
        parsed = parse_year(str(academic_year))
        if parsed:
            block["last_updated_year"] = parsed
            block["parsed_year"] = parsed


def fill_missing_from_evidence(block_type: str, block: Dict[str, Any]) -> None:
    """
    Lightweight regex-based backfill using the evidence snippet when the LLM
    left obvious fields empty. This is additive and only fills missing fields.
    """
    if not isinstance(block, dict):
        return

    snippet = ""
    if isinstance(block.get("evidence"), dict):
        snippet = block["evidence"].get("snippet") or ""
    if not snippet or len(snippet) < 10:
        return

    text = snippet.lower()

    def _extract_int(pattern: str) -> int | None:
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return None
        try:
            return int(re.sub(r"[^\d]", "", m.group(1)))
        except Exception:
            return None

    def _extract_float(pattern: str) -> float | None:
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return None
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            return None

    if block_type == "faculty_information":
        backfills = {
            "professors": _extract_int(r"professors:\s*([\d,\.]+)"),
            "associate_professors": _extract_int(r"associate professors:\s*([\d,\.]+)"),
            "assistant_professors": _extract_int(r"assistant professors:\s*([\d,\.]+)"),
            "non_teaching_staff": _extract_int(r"(?:faculty )?non[- ]teaching:?[\s]*([\d,\.]+)"),
            "year": _extract_int(r"year:\s*(\d{4})"),
        }
        for key, val in backfills.items():
            if val is not None and block.get(key) in (None, ""):
                block[key] = val
                if isinstance(val, (int, float)):
                    block.setdefault(f"{key}_num", float(val))

    elif block_type == "student_enrollment_information":
        backfills = {
            "male": _extract_int(r"male:\s*([\d,\.]+)"),
            "female": _extract_int(r"female:\s*([\d,\.]+)"),
            "academic_year": None,
        }
        # Academic year like 2023-24 or 2023–2024
        m_year = re.search(r"academic year:\s*([\d]{4}[–-]\d{2,4})", text, re.IGNORECASE)
        if m_year and block.get("academic_year") in (None, ""):
            block["academic_year"] = m_year.group(1).replace("–", "-")
        for key, val in backfills.items():
            if val is not None and block.get(key) in (None, ""):
                block[key] = val
                if isinstance(val, (int, float)):
                    block.setdefault(f"{key}_num", float(val))

    elif block_type == "infrastructure_information":
        backfills = {
            "classrooms": _extract_int(r"classrooms:\s*([\d,\.]+)"),
            "tutorial_rooms": _extract_int(r"tutorial rooms:\s*([\d,\.]+)"),
            "seminar_halls": _extract_int(r"seminar halls:\s*([\d,\.]+)"),
            "library_area_sqm": _extract_int(r"library area:\s*([\d,\.]+)"),
            "library_seating": _extract_int(r"library seating:\s*([\d,\.]+)"),
        }
        for key, val in backfills.items():
            if val is not None and block.get(key) in (None, ""):
                block[key] = val
                block.setdefault(f"{key}_num", float(val))
        # Digital library systems yes/no
        if block.get("digital_library_systems") in (None, ""):
            if "digital library systems: yes" in text or "digital library" in text:
                block["digital_library_systems"] = "yes"

    elif block_type == "lab_equipment_information":
        val = _extract_int(r"computer labs:\s*([\d,\.]+)")
        if val is not None and block.get("computer_labs") in (None, ""):
            block["computer_labs"] = val
            block.setdefault("computer_labs_num", float(val))

    elif block_type == "placement_information":
        backfills = {
            "median_salary_lpa": _extract_float(r"median salary:\s*₹?\s*([\d\.]+)"),
            "highest_salary_lpa": _extract_float(r"highest salary:\s*₹?\s*([\d\.]+)"),
        }
        if block.get("year") in (None, ""):
            m = re.search(r"placement year:\s*([\d]{4}[–-]\d{2,4}|\d{4})", text, re.IGNORECASE)
            if m:
                block["year"] = m.group(1).replace("–", "-")
        for key, val in backfills.items():
            if val is not None and block.get(key) in (None, ""):
                block[key] = val
                block.setdefault(f"{key}_num", float(val))


