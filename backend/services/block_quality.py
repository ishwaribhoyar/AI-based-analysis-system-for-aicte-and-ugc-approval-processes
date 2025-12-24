"""
Block Quality Assessment Service
Relaxed validation rules: blocks are invalid only if completeness < 25% AND no major fields present
"""

import re
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BlockQualityService:
    """Quality assessment for information blocks"""
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def check_block_quality(
        self,
        block: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """
        Check block quality: outdated, low-quality, invalid
        Returns: {
            is_outdated: bool,
            is_low_quality: bool,
            is_invalid: bool,
            outdated_reason: str | None,
            low_quality_reason: str | None,
            invalid_reason: str | None
        }
        """
        result = {
            "is_outdated": False,
            "is_low_quality": False,
            "is_invalid": False,
            "outdated_reason": None,
            "low_quality_reason": None,
            "invalid_reason": None
        }
        
        # Check outdated (extract year, if year < current_year - 2)
        outdated_check = self._check_outdated(block)
        if outdated_check["is_outdated"]:
            result["is_outdated"] = True
            result["outdated_reason"] = outdated_check["reason"]
        
        # Check low-quality (confidence < 0.50 OR text < 20 words)
        low_quality_check = self._check_low_quality(block)
        if low_quality_check["is_low_quality"]:
            result["is_low_quality"] = True
            result["low_quality_reason"] = low_quality_check["reason"]
        
        return result
    
    def _check_outdated(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Check if block contains outdated information (>2 years old) - Do NOT punish missing year"""
        from utils.parse_year import parse_year
        
        # Extract year from extracted_data
        extracted_data = block.get("extracted_data", {})
        
        # For placement_information, prefer academic_year_start/end
        if block.get("block_type") == "placement_information":
            academic_year_start = extracted_data.get("academic_year_start")
            academic_year_end = extracted_data.get("academic_year_end")
            if academic_year_start:
                parsed = parse_year(str(academic_year_start))
                if parsed:
                    extracted_year = parsed
                else:
                    extracted_year = None
            elif academic_year_end:
                parsed = parse_year(str(academic_year_end))
                if parsed:
                    extracted_year = parsed
                else:
                    extracted_year = None
            else:
                extracted_year = None
        else:
            extracted_year = None
        
        # Check parsed_year field (normalized year from parse_year)
        if extracted_year is None:
            parsed_year = extracted_data.get("parsed_year")
            if parsed_year:
                try:
                    year_val = int(parsed_year)
                    if 1900 <= year_val <= 2100:
                        extracted_year = year_val
                except (ValueError, TypeError):
                    pass
        
        # Check last_updated_year field
        if extracted_year is None:
            last_updated_year = extracted_data.get("last_updated_year")
            if last_updated_year:
                parsed = parse_year(str(last_updated_year))
                if parsed:
                    extracted_year = parsed
        
        # Fallback: look for year patterns in extracted data
        if extracted_year is None:
            years_found = []
            for key, value in extracted_data.items():
                if isinstance(value, str):
                    parsed = parse_year(value)
                    if parsed:
                        years_found.append(parsed)
                elif isinstance(value, (int, float)) and 1900 <= value <= 2100:
                    years_found.append(int(value))
            
            if years_found:
                extracted_year = max(years_found)
        
        # If no year found, do NOT mark as outdated
        if extracted_year is None:
            block["is_outdated"] = False
            return {"is_outdated": False, "reason": None}
        
        # Check if outdated: (current_year - extracted_year) > 2
        if (self.current_year - extracted_year) > 2:
            block["is_outdated"] = True
            return {
                "is_outdated": True,
                "reason": f"Information dated {extracted_year} is more than 2 years old (current: {self.current_year})"
            }
        else:
            block["is_outdated"] = False
            return {"is_outdated": False, "reason": None}
    
    def _check_low_quality(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if block has low quality.

        Low quality if:
        - Effective confidence (combination of LLM confidence and field completeness)
          is low, OR
        - Numeric parsing failed for >1 numeric-required fields.

        This is intentionally conservative: blocks with many real values should
        rarely be marked low quality.
        """
        reasons = []
        
        # Confidence components and non-null ratio
        extracted_data = block.get("extracted_data", {}) or {}
        total_fields = len(extracted_data) or 1
        non_null_fields = sum(
            1
            for v in extracted_data.values()
            if v is not None and v != "" and str(v).lower() not in ["none", "null", "n/a", "na"]
        )
        non_null_ratio = non_null_fields / total_fields if total_fields > 0 else 0.0

        raw_llm_conf = float(block.get("confidence", 0.5) or 0.5)
        # Improved blended confidence: 60% weight on non_null_ratio, 40% on LLM confidence
        effective_conf = (0.6 * non_null_ratio) + (0.4 * raw_llm_conf)

        # If we have a good amount of data (≥50%), enforce a reasonable floor
        if non_null_ratio >= 0.50:
            effective_conf = max(effective_conf, 0.75)
        elif non_null_ratio >= 0.35 and effective_conf < 0.65:
            effective_conf = 0.65

        if effective_conf < 0.50:
            reasons.append(
                f"Effective confidence ({effective_conf:.2f}) below 0.50 "
                f"(raw_llm_conf={raw_llm_conf:.2f}, non_null_ratio={non_null_ratio:.2f})"
            )
        
        # Check numeric parsing failures (if numeric fields exist but parsing failed)
        extracted_data = block.get("extracted_data", {}) or {}
        numeric_fields = ["faculty_count", "student_count", "built_up_area", "placement_rate", 
                         "lab_count", "total_intake", "admitted_students", "fsr_value"]
        parsing_failures = 0
        for field in numeric_fields:
            if field in extracted_data:
                raw_value = extracted_data.get(field)
                # Check if _num variant exists (parsed successfully)
                num_field = f"{field}_num"
                if raw_value is not None and raw_value != "" and extracted_data.get(num_field) is None:
                    # Field exists but parsing failed
                    parsing_failures += 1
        
        if parsing_failures > 1:
            reasons.append(f"Numeric parsing failed for {parsing_failures} required numeric fields")
        
        if reasons:
            return {
                "is_low_quality": True,
                "reason": "; ".join(reasons)
            }
        
        return {"is_low_quality": False, "reason": None}
    
    def check_invalid(
        self,
        block: Dict[str, Any],
        mode: str,
        ai_client=None
    ) -> Dict[str, Any]:
        """
        Check if block is invalid.
        A block is INVALID only if:
        - completeness < 20%, AND
        - no critical fields (id fields) present
        
        A block is VALID if:
        - completeness >= 40% OR
        - at least 3 major fields present
        
        Returns: {is_invalid: bool, reason: str | None}
        """
        extracted_data = block.get("extracted_data", {})
        block_type = block.get("block_type", "")
        
        if not extracted_data or not isinstance(extracted_data, dict):
            return {"is_invalid": True, "reason": "No extracted data"}
        
        # Calculate completeness: count non-null required fields
        # Get required fields for this block type
        from config.information_blocks import get_block_fields
        required_fields = get_block_fields(block_type, mode)
        total_required = len(required_fields) if required_fields else len(extracted_data)
        
        non_null_required = 0
        for field in (required_fields if required_fields else extracted_data.keys()):
            value = extracted_data.get(field)
            if value is not None and value != "" and value != "null" and str(value).lower() not in ["none", "n/a", "na"]:
                non_null_required += 1
        
        if total_required == 0:
            return {"is_invalid": True, "reason": "No required fields defined"}
        
        completeness_pct = (non_null_required / total_required) * 100 if total_required > 0 else 0
        
        # Define major fields per block type (critical/id fields) - includes both new schema and legacy fields
        major_fields_map = {
            "faculty_information": [
                "total_faculty", "faculty_count", "permanent_faculty", "visiting_faculty", 
                "phd_faculty", "non_phd_faculty", "supporting_staff", "professors", 
                "associate_professors", "assistant_professors", "fsr_value"
            ],
            "student_enrollment_information": [
                "total_students", "total_intake", "admitted_students", "student_count",
                "ug_enrollment", "pg_enrollment", "intake_capacity_ug", "intake_capacity_pg",
                "program_wise_enrollment", "foreign_students"
            ],
            "infrastructure_information": [
                "built_up_area", "built_up_area_raw", "total_classrooms", "smart_classrooms",
                "number_of_classrooms", "number_of_labs", "library_area", "library_books",
                "digital_library_resources", "computers_available", "hostel_capacity"
            ],
            "lab_equipment_information": [
                "lab_count", "total_labs", "advanced_labs", "major_equipment_count",
                "major_equipments", "major_equipment", "equipment_sufficiency", "computers_in_labs"
            ],
            "safety_compliance_information": [
                "fire_safety_certificate", "fire_safety_certificate_raw", 
                "building_safety_certificate", "building_stability_certificate_raw",
                "environmental_clearance", "safety_officer_appointed"
            ],
            "academic_calendar_information": [
                "start_date", "end_date", "academic_year_start", "academic_year_end",
                "total_weeks", "total_working_days", "academic_year"
            ],
            "fee_structure_information": [
                "annual_fee", "tuition_fee_ug_raw", "tuition_fee_pg_raw",
                "hostel_fee", "hostel_fee_raw", "transport_fee", "transport_fee_raw"
            ],
            "placement_information": [
                "placement_rate", "placement_rate_raw", "average_salary", "highest_salary",
                "highest_salary_raw", "median_salary_raw", "eligible_students", "students_placed",
                "total_placements", "top_recruiters"
            ],
            "research_innovation_information": [
                "publications", "patents", "patents_filed", "patents_granted",
                "funded_projects", "publication_count", "research_funding_raw"
            ],
            "mandatory_committees_information": [
                "anti_ragging_committee", "anti_ragging", "icc_committee", "icc",
                "grievance_committee", "grievance_redressal", "sc_st_committee", "scst_cell", "iqac"
            ]
        }
        
        major_fields = major_fields_map.get(block_type, [])
        
        # Count major fields present
        major_fields_present = 0
        for field in major_fields:
            value = extracted_data.get(field)
            # Also check _num variant
            num_value = extracted_data.get(f"{field}_num")
            if (value is not None and value != "" and value != "null" and str(value).lower() not in ["none", "n/a", "na"]) or \
               (num_value is not None):
                if isinstance(value, (int, float)) and value > 0:
                    major_fields_present += 1
                elif isinstance(value, str) and value.strip():
                    major_fields_present += 1
                elif isinstance(value, bool):
                    major_fields_present += 1
                elif isinstance(value, (list, dict)) and len(value) > 0:
                    major_fields_present += 1
                elif num_value is not None:
                    major_fields_present += 1
        
        # Count numeric fields present (never zero-out blocks with valid numeric data)
        numeric_field_count = 0
        numeric_field_patterns = ["_num", "count", "enrollment", "faculty", "students", "area", "rate", "salary", "books", "labs", "publications", "patents"]
        for key, value in extracted_data.items():
            if any(pattern in key.lower() for pattern in numeric_field_patterns):
                if isinstance(value, (int, float)) and value > 0:
                    numeric_field_count += 1
                elif isinstance(value, str) and value.strip() and value.lower() not in ["none", "null", "n/a", "na"]:
                    # Check if it's a numeric string
                    try:
                        float(str(value).replace(",", "").replace("%", "").strip())
                        numeric_field_count += 1
                    except (ValueError, AttributeError):
                        pass
        
        # Block is VALID if:
        # - completeness >= 40% OR
        # - at least 3 major fields present OR
        # - at least 3 numeric fields present (never zero-out blocks with valid numeric data)
        if completeness_pct >= 40 or major_fields_present >= 3 or numeric_field_count >= 3:
            return {"is_invalid": False, "reason": None}
        
        # Block is INVALID only if completeness < 20% AND no major fields present AND no numeric fields
        if completeness_pct < 20 and major_fields_present == 0 and numeric_field_count == 0:
            return {
                "is_invalid": True,
                "reason": f"Completeness {completeness_pct:.1f}% < 20%, no major fields, and no numeric fields present"
            }
        
        # Basic validation: check for negative numbers (only for counts)
        for key, value in extracted_data.items():
            if isinstance(value, (int, float)) and value < 0:
                if "count" in key.lower() or "number" in key.lower():
                    return {
                        "is_invalid": True,
                        "reason": f"Negative value for {key}: {value}"
                    }
        
        # Check for impossible percentages (>100%)
        for key, value in extracted_data.items():
            if "percentage" in key.lower() or "rate" in key.lower() or "percent" in key.lower():
                if isinstance(value, (int, float)) and value > 100:
                    return {
                        "is_invalid": True,
                        "reason": f"Impossible percentage for {key}: {value}%"
                    }
        
        return {"is_invalid": False, "reason": None}
