"""
One-Shot Block Extraction Service
Extracts ALL information blocks in a single GPT-5 Nano call using FULL CONTEXT.
Mode-specific: AICTE (10 blocks) and UGC (10 blocks)
"""

import logging
from typing import Dict, Any
import json

from ai.openai_client import OpenAIClient
from utils.validators import parse_json_safely
from ai.openai_utils import safe_openai_call
from config.information_blocks import get_information_blocks, get_block_fields

logger = logging.getLogger(__name__)


class OneShotExtractionService:
    """One-shot extraction of all information blocks from full-context text."""

    def __init__(self):
        self.ai_client = OpenAIClient()

    def _build_schema_json(self, mode: str, new_university: bool = False) -> str:
        """
        Build mode-specific JSON schema for extraction.

        NOTE: For AICTE this follows the strict JSON schema used in the
        system/user prompt, wrapped inside a top-level "blocks" object.
        For UGC we retain the previous, more free-form pseudo-schema.
        """
        mode_lower = mode.lower()
        if mode_lower == "aicte":
            # Strict AICTE schema wrapped inside a "blocks" object.
            return """{
  "blocks": {
    "faculty_information": {
      "total_faculty": number | null,
      "permanent_faculty": number | null,
      "visiting_faculty": number | null,
      "phd_faculty": number | null,
      "non_phd_faculty": number | null,
      "supporting_staff": number | null,
      "department_wise_faculty": { "CSE": number|null, "ECE": number|null, "ME": number|null, "CE": number|null, "MBA": number|null },
      "last_year_faculty_data": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "student_enrollment_information": {
      "total_students": number|null,
      "ug_enrollment": number|null,
      "pg_enrollment": number|null,
      "intake_capacity_ug": number|null,
      "intake_capacity_pg": number|null,
      "foreign_students": number|null,
      "intake_proposal": string|null,
      "program_justification": string|null,
      "last_year_enrollment_data": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "infrastructure_information": {
      "total_classrooms": number|null,
      "smart_classrooms": number|null,
      "built_up_area_raw": string|null,
      "library_books": number|null,
      "digital_library_resources": number|null,
      "computers_available": number|null,
      "hostel_capacity": number|null,
      "land_document": string|null,
      "building_plan": string|null,
      "3_year_infrastructure_plan": string|null,
      "3_year_financial_projection": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "lab_equipment_information": {
      "total_labs": number|null,
      "advanced_labs": number|null,
      "major_equipment_count": number|null,
      "computers_in_labs": number|null,
      "annual_lab_budget_raw": string|null,
      "major_equipment": [string] | null,
      "lab_establishment_plan": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "safety_compliance_information": {
      "fire_safety_certificate_raw": string|null,
      "fire_safety_certificate_valid_till": string|null,
      "building_stability_certificate_raw": string|null,
      "safety_officer_appointed": boolean|null,
      "disaster_management_plan": string|null,
      "last_year_safety_certificates": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "academic_calendar_information": {
      "academic_year_start": string|null,
      "academic_year_end": string|null,
      "total_working_days": number|null,
      "exam_schedule_published": boolean|null,
      "holiday_list_published": boolean|null,
      "3_year_academic_plan": string|null,
      "last_year_academic_calendar": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "fee_structure_information": {
      "tuition_fee_ug_raw": string|null,
      "tuition_fee_pg_raw": string|null,
      "hostel_fee_raw": string|null,
      "transport_fee_raw": string|null,
      "other_charges_raw": string|null,
      "scholarships_available": boolean|null,
      "3_year_financial_projection": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "placement_information": {
      "eligible_students": number|null,
      "students_placed": number|null,
      "placement_rate_raw": string|null,
      "median_salary_raw": string|null,
      "highest_salary_raw": string|null,
      "top_recruiters": [string] | null,
      "last_year_placement_data": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "research_innovation_information": {
      "publications": number|null,
      "patents_filed": number|null,
      "patents_granted": number|null,
      "funded_projects": number|null,
      "research_funding_raw": string|null,
      "last_year_research_data": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    },
    "mandatory_committees_information": {
      "anti_ragging": boolean|null,
      "icc": boolean|null,
      "grievance_redressal": boolean|null,
      "sc_st_committee": boolean|null,
      "iqac": boolean|null,
      "last_year_committee_updates": string|null,
      "evidence": { "snippet": string|null, "page": number|null }
    }
  }
}"""

        # UGC mode keeps the more free-form pseudo schema used previously.
        required_blocks = get_information_blocks(mode, new_university)
        schema_parts = []
        if mode_lower == "ugc":
            schema_parts.append('  "faculty_and_staffing": {')
            schema_parts.append('    "faculty_count": int|null,')
            schema_parts.append('    "qualification_breakdown": {},')
            schema_parts.append('    "designation_breakdown": {},')
            schema_parts.append('    "faculty_onboarding_plan": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "student_enrollment_and_programs": {')
            schema_parts.append('    "student_count": int|null,')
            schema_parts.append('    "program_wise_enrollment": {},')
            schema_parts.append('    "proposed_programs": [],')
            schema_parts.append('    "last_year_exam_results": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "infrastructure_and_land_building": {')
            schema_parts.append('    "built_up_area": float|null,')
            schema_parts.append('    "land_area": float|null,')
            schema_parts.append('    "library_area": float|null,')
            schema_parts.append('    "land_ownership": string|null,')
            schema_parts.append('    "campus_details": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "academic_governance_and_bodies": {')
            schema_parts.append('    "board_of_governors": bool|null,')
            schema_parts.append('    "academic_council": bool|null,')
            schema_parts.append('    "finance_committee": bool|null,')
            schema_parts.append('    "governance_structure": string|null,')
            schema_parts.append('    "trust_act_document": string|null,')
            schema_parts.append('    "last_year_governance_compliance": string|null,')
            schema_parts.append('    "last_year_committee_reports": string|null,')
            schema_parts.append('    "affiliation_request": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "financial_information": {')
            schema_parts.append('    "annual_budget": float|null,')
            schema_parts.append('    "revenue": float|null,')
            schema_parts.append('    "expenditure": float|null,')
            schema_parts.append('    "budget_plan": float|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "research_and_publications": {')
            schema_parts.append('    "publications": int|null,')
            schema_parts.append('    "citations": int|null,')
            schema_parts.append('    "funded_projects": int|null,')
            schema_parts.append('    "last_year_research_data": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "iqac_quality_assurance": {')
            schema_parts.append('    "iqac_established": bool|null,')
            schema_parts.append('    "accreditation_status": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "learning_resources_library_ict": {')
            schema_parts.append('    "library_area": float|null,')
            schema_parts.append('    "ict_facilities": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  },')
            
            schema_parts.append('  "regulatory_compliance": {')
            schema_parts.append('    "ugc_regulations_2018_compliance": bool|null,')
            schema_parts.append('    "statutory_committees": {},')
            schema_parts.append('    "affiliation_request": string|null,')
            schema_parts.append('    "last_updated_year": int|null')
            schema_parts.append('  }')
            
            # Only include future_academic_plan for new universities
            if new_university:
                schema_parts.append(',')
                schema_parts.append('  "future_academic_plan": {')
                schema_parts.append('    "expansion_plan": string|null,')
                schema_parts.append('    "new_programs": [],')
                schema_parts.append('    "strategic_vision": string|null,')
                schema_parts.append('    "proposed_programs": [],')
                schema_parts.append('    "last_updated_year": int|null')
                schema_parts.append('  }')
        
        return "{\n" + "\n".join(schema_parts) + "\n}"

    def extract_all_blocks(self, full_context_text: str, mode: str, new_university: bool = False) -> Dict[str, Any]:
        """
        Extract ALL information blocks in one LLM call using FULL CONTEXT.

        full_context_text is the concatenation of:
        - Docling/pypdf full text from all PDFs
        - Tables markdown
        - Structured sections
        - OCR fallback text (if any)

        Returns:
            {
                "blocks": {
                    "block_type": {...},
                    ...
                },
                "confidence": float (0–1),
                "evidence": []
            }
        """
        # Token-safety: if text is extremely long, trim from START.
        # GPT-5 Nano supports ~80k tokens; we cap to ~75k characters of context.
        max_chars = 75_000
        if len(full_context_text) > max_chars:
            full_context_text = full_context_text[-max_chars:]
            logger.info(f"Truncated full_context_text to {len(full_context_text)} characters (kept last {max_chars})")

        # Get mode-specific blocks (conditional for UGC)
        required_blocks = get_information_blocks(mode, new_university)
        
        # Build flexible hybrid extraction prompt for AICTE mode
        mode_lower = mode.lower()
        if mode_lower == "aicte":
            system_message = (
                "You are an AICTE-compliant institutional information extractor. "
                "Your job is to extract as many factual values as possible from the given PDF text.\n\n"
                "IMPORTANT RULES:\n"
                "1. Extract ONLY values explicitly present in the text. Never infer or hallucinate.\n"
                "2. Always return:\n"
                "   - raw value (as string, e.g., \"₹85,000\", \"4.2 LPA\", \"18,500 sq. m\")\n"
                "   - parsed numeric value (*_num field, e.g., 85000, 4.2, 18500)\n"
                "3. Accept aliases and map to canonical keys:\n"
                "   - \"Total Students Eligible\", \"Total Students\", \"Students Strength\" → total_students\n"
                "   - \"Permanent Faculty\", \"Permanent Staff\" → permanent_faculty\n"
                "   - \"Total Area (sq.ft)\", \"Built-up Area\" → built_up_area_raw\n"
                "   - \"Library Books\", \"Total Books\" → library_books\n"
                "   - \"Major Equipment Count\", \"Equipment Count\" → major_equipment_count\n"
                "   - \"Students Placed\", \"Placed Students\" → students_placed\n"
                "   - \"Placement Rate\", \"Placement Percentage\" → placement_rate_raw\n"
                "   - \"Highest Salary\", \"Maximum Salary\" → highest_salary_raw\n"
                "4. If structure differs, still output the matching field flat.\n"
                "5. Never return null if the text clearly contains the value.\n"
                "6. Nested objects are optional. Flat values are acceptable.\n"
                "7. Always include all schema keys; use null ONLY when NO matching information exists.\n"
                "8. When multiple values exist, choose the MOST specific one.\n\n"
                "You MUST output JSON with this structure:\n"
                "{\n"
                '  "blocks": {\n'
                '    "faculty_information": {},\n'
                '    "student_enrollment_information": {},\n'
                '    "infrastructure_information": {},\n'
                '    "lab_equipment_information": {},\n'
                '    "safety_compliance_information": {},\n'
                '    "academic_calendar_information": {},\n'
                '    "fee_structure_information": {},\n'
                '    "placement_information": {},\n'
                '    "research_innovation_information": {},\n'
                '    "mandatory_committees_information": {}\n'
                "  }\n"
                "}\n\n"
                "For each block, extract ALL values that exist in the text. "
                "Synonyms, alternative phrasings, and reordered sections MUST still map to correct fields."
            )
        else:
            system_message = (
                "You are a government-grade information extraction engine used by "
                f"{mode.upper()} reviewers. Extract only factual information that explicitly "
                "appears in the text. Never infer, never guess, never hallucinate. "
                "If a field is not explicitly present, return null. "
                "Return ONLY valid JSON matching the schema.\n\n"
                "You must capture structured data including nested objects, arrays, tables, "
                "program-wise enrollment, department-wise faculty, lab distributions, "
                "equipment lists, recruiter lists, and committee presence flags."
            )

        schema_json = self._build_schema_json(mode)

        if mode.lower() == "aicte":
            # Ground-truth example for sample.pdf to guide the model.
            ground_truth_example = """
GROUND-TRUTH EXAMPLE (for sample.pdf):
{
  "blocks": {
    "faculty_information": {
      "total_faculty": 112,
      "permanent_faculty": 98,
      "visiting_faculty": 14,
      "phd_faculty": 52,
      "non_phd_faculty": 60,
      "supporting_staff": 23,
      "department_wise_faculty": {"CSE":24,"ECE":15,"ME":18,"CE":12,"MBA":13},
      "evidence":{"snippet":"Total Faculty: 112","page":1}
    },
    "student_enrollment_information": {
      "total_students": 1840,
      "ug_enrollment": 1520,
      "pg_enrollment": 320,
      "intake_capacity_ug": 1600,
      "intake_capacity_pg": 350,
      "foreign_students": 28,
      "evidence": {"snippet":"Total Students: 1840","page":1}
    },
    "infrastructure_information": {
      "total_classrooms": 34,
      "smart_classrooms": 22,
      "built_up_area_raw": "185,000 sq.ft",
      "library_books": 32500,
      "digital_library_resources": 1240,
      "computers_available": 485,
      "hostel_capacity": 800,
      "evidence":{"snippet":"Total Area (sq.ft): 185,000","page":1}
    },
    "placement_information": {
      "eligible_students": 420,
      "students_placed": 362,
      "placement_rate_raw": "86.19%",
      "median_salary_raw": "6.5 LPA",
      "highest_salary_raw": "18 LPA",
      "top_recruiters": ["Infosys","TCS","Wipro","Accenture"],
      "evidence":{"snippet":"Placement Rate: 86.19%","page":1}
    }
  }
}
"""
        else:
            ground_truth_example = ""

        if mode.lower() == "aicte":
            user_message = f"""SCHEMA (AICTE blocks — return an object with "blocks": {{
  <block_key>: {{ ... }}
}}):

{schema_json}

{ground_truth_example}

TEXT TO ANALYZE:
----------------
{full_context_text}
----------------

EXTRACTION GUIDELINES:
- Extract ALL values that exist in the text, even if labels differ slightly.
- Map synonyms automatically (e.g., "Total Students Eligible" → eligible_students).
- NEVER return null when the value clearly exists in text.
- ALWAYS output at least the simple flat fields, even if nested fields fail.
- Nested dictionaries are optional; flat values are acceptable.
- Use the sample above as guidance only, NOT as strict formatting.
- When multiple candidate matches exist, choose the most specific one (prefer lines with block headings or numeric labels).
- For numeric fields, extract the number even if units differ (postprocess will normalize).
- Return ONLY valid JSON, no explanations.
"""
        else:
            user_message = f"""Extract the following {len(required_blocks)} information blocks in STRICT JSON.

{schema_json}

TEXT TO ANALYZE:
----------------
{full_context_text}
----------------

Rules:
- Extract ONLY explicit data from the text.
- If unclear or not explicitly stated → null.
- Do NOT infer or fabricate.
- Return ONLY JSON, no explanations.
"""

        try:
            # Retry wrapper around safe_openai_call for robustness
            import time

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = safe_openai_call(
                        self.ai_client.client,
                        self.ai_client.primary_model,
                        [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.0,
                    )
                    break
                except Exception as call_err:
                    logger.warning(f"Extraction attempt {attempt + 1} failed: {call_err}")
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(1.0)

            result_text = response.choices[0].message.content
            result = parse_json_safely(result_text)

            # Normalize result into expected block structure
            # Result may either be { "blocks": { ... } } (new AICTE schema)
            # or flat { "faculty_information": {...}, ... } (older style).
            root_blocks = result.get("blocks") if isinstance(result, dict) and "blocks" in result else result

            # Helper to flatten nested structures (e.g., {"totals": {"total": 112}} -> {"total": 112})
            def flatten_nested_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
                """Recursively flatten nested dictionaries, preserving top-level keys."""
                result = {}
                for key, value in d.items():
                    if key == "evidence":  # Preserve evidence as-is
                        result[key] = value
                        continue
                    new_key = f"{prefix}_{key}" if prefix else key
                    if isinstance(value, dict):
                        # Flatten nested dict, but also try to map common nested patterns
                        flattened = flatten_nested_dict(value, new_key)
                        result.update(flattened)
                        # Also try direct mapping for common patterns
                        if "total" in value:
                            result[key] = value.get("total")
                        elif "count" in value:
                            result[key] = value.get("count")
                        elif "permanent" in value and "faculty" in key.lower():
                            result["permanent_faculty"] = value.get("permanent")
                        elif "visiting" in value and "faculty" in key.lower():
                            result["visiting_faculty"] = value.get("visiting")
                    elif isinstance(value, list):
                        result[key] = value  # Preserve lists as-is
                    else:
                        result[key] = value
                return result
            
            # Alias mapping for common variations
            alias_map = {
                "faculty_information": {
                    "faculty_with_phd": "phd_faculty",
                    "faculty_without_phd": "non_phd_faculty",
                    "permanent_staff": "permanent_faculty",
                    "visiting_staff": "visiting_faculty",
                },
                "student_enrollment_information": {
                    "total_enrollment": "total_students",
                    "headcount": "total_students",
                    "undergraduate": "ug_enrollment",
                    "postgraduate": "pg_enrollment",
                },
                "infrastructure_information": {
                    "total_area": "built_up_area_raw",
                    "campus_area": "built_up_area_raw",
                    "area": "built_up_area_raw",
                    "number_of_books": "library_books",
                },
                "placement_information": {
                    "placed_students": "students_placed",
                    "placement_percentage": "placement_rate_raw",
                    "max_salary": "highest_salary_raw",
                }
            }

            extracted_blocks: Dict[str, Any] = {}
            for block_type in required_blocks:
                block_payload = root_blocks.get(block_type, {}) if isinstance(root_blocks, dict) else {}
                block_payload = block_payload or {}
                if not isinstance(block_payload, dict):
                    block_payload = {}
                
                # Flatten nested structures
                block_payload = flatten_nested_dict(block_payload)
                
                # Apply alias mappings
                block_aliases = alias_map.get(block_type, {})
                for alias_key, canonical_key in block_aliases.items():
                    if alias_key in block_payload and canonical_key not in block_payload:
                        block_payload[canonical_key] = block_payload.pop(alias_key)
                
                # Get expected fields for this block
                block_fields = get_block_fields(block_type, mode)
                required_fields = block_fields.get("required_fields", [])
                optional_fields = block_fields.get("optional_fields", [])
                
                # Ensure all expected fields exist, defaulting to None
                for field in required_fields + optional_fields:
                    if field not in block_payload:
                        block_payload[field] = None
                
                # Always add last_updated_year if not present
                if "last_updated_year" not in block_payload:
                    block_payload["last_updated_year"] = None

                extracted_blocks[block_type] = block_payload

            # Post-process: parse numeric fields and year fields
            from utils.parse_numeric import parse_numeric
            from utils.parse_year import parse_year
            
            for block_type, block_data in extracted_blocks.items():
                if not isinstance(block_data, dict):
                    continue
                
                # Parse numeric fields and add _num variants
                # Include both new strict schema fields and legacy fields for backward compatibility
                numeric_fields = [
                    # New strict schema fields
                    "total_faculty", "permanent_faculty", "visiting_faculty", "phd_faculty", 
                    "non_phd_faculty", "supporting_staff",
                    "total_students", "ug_enrollment", "pg_enrollment", "intake_capacity_ug", 
                    "intake_capacity_pg", "foreign_students",
                    "total_classrooms", "smart_classrooms", "library_books", "digital_library_resources",
                    "computers_available", "hostel_capacity",
                    "total_labs", "advanced_labs", "major_equipment_count", "computers_in_labs",
                    "eligible_students", "students_placed",
                    "patents_filed", "patents_granted",
                    # Legacy fields (preserved for backward compatibility)
                    "faculty_count", "student_count", "total_intake", "admitted_students",
                    "built_up_area", "placement_rate", "average_salary", "highest_salary",
                    "lab_count", "fsr_value", "annual_fee", "hostel_fee", "transport_fee",
                    "publications", "patents", "funded_projects", "publication_count",
                    "library_area", "number_of_classrooms", "number_of_labs"
                ]
                
                for field in numeric_fields:
                    if field in block_data:
                        raw_value = block_data[field]
                        if raw_value is not None and raw_value != "":
                            parsed_num = parse_numeric(str(raw_value))
                            if parsed_num is not None:
                                block_data[f"{field}_num"] = parsed_num
                
                # Parse year fields
                year_fields = ["last_updated_year", "academic_year"]
                for field in year_fields:
                    if field in block_data:
                        raw_value = block_data[field]
                        if raw_value is not None and raw_value != "":
                            parsed_year = parse_year(str(raw_value))
                            if parsed_year:
                                block_data["parsed_year"] = parsed_year
                                # Also update the original field with normalized year
                                block_data[field] = parsed_year

            # Compute confidence = proportion of non-null primitive fields
            total_fields = 0
            non_null_fields = 0
            for key, block_data in extracted_blocks.items():
                if isinstance(block_data, dict):
                    for field_name, value in block_data.items():
                        # Skip container fields and _num variants for confidence calculation
                        if isinstance(value, (dict, list)) or field_name.endswith("_num"):
                            continue
                        total_fields += 1
                        if value is not None and value != "":
                            non_null_fields += 1

            confidence = non_null_fields / total_fields if total_fields > 0 else 0.0

            return {
                "blocks": extracted_blocks,
                "confidence": confidence,
                "evidence": [],  # Evidence is generated later from full_context_text
            }

        except Exception as e:
            logger.error(f"One-shot extraction error: {e}")
            import traceback

            logger.error(traceback.format_exc())

            # Return empty blocks on error
            required_blocks = get_information_blocks(mode, new_university)
            empty_blocks: Dict[str, Any] = {key: {} for key in required_blocks}

            return {
                "blocks": empty_blocks,
                "confidence": 0.0,
                "evidence": [],
            }
