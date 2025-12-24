"""
Information Block Definitions
Mode-specific blocks: AICTE (10 blocks) and UGC (10 blocks)
"""

from typing import Dict, List, Any

# AICTE - 10 Mandatory Information Blocks
AICTE_BLOCKS = [
    "faculty_information",
    "student_enrollment_information",
    "infrastructure_information",
    "lab_equipment_information",
    "safety_compliance_information",
    "academic_calendar_information",
    "fee_structure_information",
    "placement_information",
    "research_innovation_information",
    "mandatory_committees_information"
]

# UGC - 10 Mandatory Information Blocks
UGC_BLOCKS = [
    "faculty_and_staffing",
    "student_enrollment_and_programs",
    "infrastructure_and_land_building",
    "academic_governance_and_bodies",
    "financial_information",
    "research_and_publications",
    "iqac_quality_assurance",
    "learning_resources_library_ict",
    "regulatory_compliance",
    "future_academic_plan"  # Only populated for new universities
]

# Block descriptions for semantic classification
BLOCK_DESCRIPTIONS = {
    # AICTE Blocks
    "faculty_information": {
        "name": "Faculty Information",
        "description": "Information about teaching staff, faculty members, their qualifications, designations, departments, and faculty strength",
        "keywords": ["faculty", "teacher", "professor", "staff", "educator", "instructor", "teaching staff", "faculty strength", "qualification", "designation"],
        "synonyms": ["teaching staff", "educators", "academic staff", "faculty members", "teaching faculty"]
    },
    "student_enrollment_information": {
        "name": "Student Enrollment Information",
        "description": "Data about student enrollment, intake, student count, program-wise enrollment, and student demographics",
        "keywords": ["student", "enrollment", "intake", "admission", "student count", "total students", "enrolled", "student strength"],
        "synonyms": ["student enrollment", "student intake", "enrolled students", "student population", "student body"]
    },
    "infrastructure_information": {
        "name": "Infrastructure Information",
        "description": "Details about buildings, classrooms, built-up area, facilities, campus infrastructure, and physical assets",
        "keywords": ["infrastructure", "building", "campus", "classroom", "built-up area", "area", "facility", "facilities", "campus area"],
        "synonyms": ["built-up area", "campus infrastructure", "physical infrastructure", "building area", "campus facilities"]
    },
    "lab_equipment_information": {
        "name": "Lab & Equipment Information",
        "description": "Information about laboratories, equipment, lab count, equipment specifications, and lab facilities",
        "keywords": ["lab", "laboratory", "equipment", "lab equipment", "instruments", "lab count", "laboratory facilities"],
        "synonyms": ["laboratory", "lab facilities", "equipment list", "lab instruments", "laboratory equipment"]
    },
    "safety_compliance_information": {
        "name": "Safety & Compliance Information",
        "description": "Safety certificates, fire NOC, building stability certificates, safety compliance, and regulatory approvals",
        "keywords": ["safety", "fire", "noc", "certificate", "compliance", "fire safety", "fire noc", "building stability", "safety certificate"],
        "synonyms": ["fire NOC", "safety certificate", "fire safety certificate", "compliance certificate", "safety compliance"]
    },
    "academic_calendar_information": {
        "name": "Academic Calendar Information",
        "description": "Academic year schedules, semester dates, holidays, exam schedules, academic events, and academic calendar",
        "keywords": ["calendar", "academic calendar", "schedule", "semester", "academic year", "holiday", "exam", "academic schedule"],
        "synonyms": ["academic calendar", "academic schedule", "semester schedule", "academic year calendar", "institutional calendar"]
    },
    "fee_structure_information": {
        "name": "Fee Structure Information",
        "description": "Fee details, tuition fees, fee structure, payment schedules, fee breakdown, and financial charges",
        "keywords": ["fee", "fees", "tuition", "fee structure", "payment", "tuition fee", "fee breakdown", "charges"],
        "synonyms": ["fee structure", "tuition fees", "fee details", "payment structure", "fee schedule"]
    },
    "placement_information": {
        "name": "Placement Information",
        "description": "Placement statistics, job placements, placement percentage, company names, salary data, and career outcomes",
        "keywords": ["placement", "job", "career", "recruitment", "placement rate", "placement percentage", "salary", "company"],
        "synonyms": ["placement data", "career outcomes", "job placement", "placement statistics", "recruitment data"]
    },
    "research_innovation_information": {
        "name": "Research & Innovation Information",
        "description": "Research publications, research papers, citations, research projects, innovation, and academic research",
        "keywords": ["research", "publication", "paper", "journal", "citation", "research paper", "innovation", "research project"],
        "synonyms": ["research publications", "research papers", "academic research", "research output", "publications"]
    },
    "mandatory_committees_information": {
        "name": "Mandatory Committees Information",
        "description": "Statutory committees, mandatory committees, committee members, committee structure, and governance committees",
        "keywords": ["committee", "statutory", "board", "council", "mandatory committee", "committee members", "governance"],
        "synonyms": ["statutory committees", "mandatory committees", "governance committees", "committee structure", "board members"]
    },
    # UGC Blocks
    "faculty_and_staffing": {
        "name": "Faculty and Staffing",
        "description": "Faculty members, teaching staff, qualifications, designations, and staffing details",
        "keywords": ["faculty", "staffing", "teacher", "professor", "staff", "qualification", "designation"],
        "synonyms": ["teaching staff", "academic staff", "faculty members"]
    },
    "student_enrollment_and_programs": {
        "name": "Student Enrollment and Programs",
        "description": "Student enrollment data, program offerings, intake, and student demographics",
        "keywords": ["student", "enrollment", "program", "intake", "admission", "student count"],
        "synonyms": ["student enrollment", "programs", "student intake"]
    },
    "infrastructure_and_land_building": {
        "name": "Infrastructure and Land Building",
        "description": "Land ownership, building details, infrastructure, built-up area, and physical assets",
        "keywords": ["infrastructure", "land", "building", "campus", "built-up area", "area"],
        "synonyms": ["land and building", "campus infrastructure", "physical infrastructure"]
    },
    "academic_governance_and_bodies": {
        "name": "Academic Governance and Bodies",
        "description": "Academic governance structure, bodies, boards, councils, and governance committees",
        "keywords": ["governance", "academic", "board", "council", "body", "committee"],
        "synonyms": ["academic governance", "governance bodies", "academic bodies"]
    },
    "financial_information": {
        "name": "Financial Information",
        "description": "Financial data, budget, revenue, expenditure, and financial viability",
        "keywords": ["financial", "budget", "revenue", "expenditure", "finance", "funding"],
        "synonyms": ["financial data", "budget information", "financial viability"]
    },
    "research_and_publications": {
        "name": "Research and Publications",
        "description": "Research output, publications, citations, research projects, and academic research",
        "keywords": ["research", "publication", "citation", "research project", "journal"],
        "synonyms": ["research output", "publications", "academic research"]
    },
    "iqac_quality_assurance": {
        "name": "IQAC Quality Assurance",
        "description": "Internal Quality Assurance Cell (IQAC) information, quality assurance measures, and accreditation",
        "keywords": ["iqac", "quality assurance", "accreditation", "quality", "assurance"],
        "synonyms": ["IQAC", "quality assurance", "internal quality assurance"]
    },
    "learning_resources_library_ict": {
        "name": "Learning Resources Library ICT",
        "description": "Library resources, ICT facilities, learning resources, and digital infrastructure",
        "keywords": ["library", "ict", "learning resources", "digital", "resources"],
        "synonyms": ["library resources", "ICT facilities", "learning resources"]
    },
    "regulatory_compliance": {
        "name": "Regulatory Compliance",
        "description": "Regulatory compliance, UGC regulations, statutory compliance, and mandatory disclosures",
        "keywords": ["regulatory", "compliance", "ugc regulations", "statutory", "disclosure"],
        "synonyms": ["regulatory compliance", "UGC compliance", "statutory compliance"]
    },
    "future_academic_plan": {
        "name": "Future Academic Plan",
        "description": "Future academic plans, expansion plans, and strategic vision (only for new universities)",
        "keywords": ["future", "plan", "academic plan", "expansion", "strategic", "vision"],
        "synonyms": ["future plan", "academic plan", "expansion plan"]
    }
}

# Mode-specific field requirements for each block
BLOCK_FIELDS = {
    "aicte": {
        "faculty_information": {
            "required_fields": ["total_faculty"],
            # NOTE: All fields from new strict schema are included as optional
            # to preserve backward compatibility with existing code that may reference old keys.
            "optional_fields": [
                # New strict schema fields
                "permanent_faculty",
                "visiting_faculty",
                "phd_faculty",
                "non_phd_faculty",
                "supporting_staff",
                "department_wise_faculty",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "faculty_count",
                "professors",
                "associate_professors",
                "assistant_professors",
                "fsr_value",
                "non_teaching_staff",
                "last_updated_year",
            ]
        },
        "student_enrollment_information": {
            "required_fields": ["total_students"],
            "optional_fields": [
                # New strict schema fields
                "ug_enrollment",
                "pg_enrollment",
                "intake_capacity_ug",
                "intake_capacity_pg",
                "foreign_students",
                "intake_proposal",
                "program_justification",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "total_intake",
                "admitted_students",
                "program_wise_enrollment",
                "male",
                "female",
                "last_updated_year",
                "last_year_enrollment_data",
            ]
        },
        "infrastructure_information": {
            "required_fields": ["built_up_area_raw"],
            "optional_fields": [
                # New strict schema fields
                "total_classrooms",
                "smart_classrooms",
                "library_books",
                "digital_library_resources",
                "computers_available",
                "hostel_capacity",
                "land_document",
                "building_plan",
                "3_year_infrastructure_plan",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "built_up_area",
                "number_of_classrooms",
                "number_of_labs",
                "library_area",
                "built_up_area_sqm",
                "classrooms",
                "tutorial_rooms",
                "seminar_halls",
                "library_area_sqm",
                "library_seating",
                "digital_library_systems",
                "last_updated_year",
                "3_year_financial_projection",
            ]
        },
        "lab_equipment_information": {
            "required_fields": ["total_labs"],
            "optional_fields": [
                # New strict schema fields
                "advanced_labs",
                "major_equipment_count",
                "computers_in_labs",
                "annual_lab_budget_raw",
                "major_equipment",
                "lab_establishment_plan",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "lab_count",
                "major_equipments",
                "equipment_sufficiency",
                "computer_labs",
                "department_labs",
                "major_equipment_list",
                "last_updated_year",
            ]
        },
        "safety_compliance_information": {
            "required_fields": ["fire_safety_certificate_raw"],
            "optional_fields": [
                # New strict schema fields
                "fire_safety_certificate_valid_till",
                "building_stability_certificate_raw",
                "safety_officer_appointed",
                "disaster_management_plan",
                "safety_fire_noc",
                "sanitary_certificate",
                "last_year_safety_certificates",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "fire_safety_certificate",
                "building_safety_certificate",
                "environmental_clearance",
                "last_updated_year",
            ]
        },
        "academic_calendar_information": {
            "required_fields": ["academic_year_start"],
            "optional_fields": [
                # New strict schema fields
                "academic_year_end",
                "total_working_days",
                "exam_schedule_published",
                "holiday_list_published",
                "3_year_academic_plan",
                "3_year_infrastructure_plan",
                "3_year_financial_plan",
                "last_year_academic_calendar",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "start_date",
                "end_date",
                "total_weeks",
                "academic_year",
                "last_updated_year",
            ]
        },
        "fee_structure_information": {
            "required_fields": ["tuition_fee_ug_raw"],
            "optional_fields": [
                # New strict schema fields
                "tuition_fee_pg_raw",
                "hostel_fee_raw",
                "transport_fee_raw",
                "other_charges_raw",
                "scholarships_available",
                "3_year_financial_projection",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "annual_fee",
                "hostel_fee",
                "transport_fee",
                "last_updated_year",
            ]
        },
        "placement_information": {
            "required_fields": ["eligible_students"],
            "optional_fields": [
                # New strict schema fields
                "students_placed",
                "placement_rate_raw",
                "median_salary_raw",
                "highest_salary_raw",
                "top_recruiters",
                "last_year_placement_data",
                "nba_nirf_data",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "placement_rate",
                "average_salary",
                "highest_salary",
                "median_salary_lpa",
                "highest_salary_lpa",
                "last_updated_year",
            ]
        },
        "research_innovation_information": {
            "required_fields": ["publications"],
            "optional_fields": [
                # New strict schema fields
                "patents_filed",
                "patents_granted",
                "funded_projects",
                "research_funding_raw",
                "last_year_research_data",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "patents",
                "last_updated_year",
            ]
        },
        "mandatory_committees_information": {
            "required_fields": ["anti_ragging"],
            "optional_fields": [
                # New strict schema fields
                "icc",
                "grievance_redressal",
                "sc_st_committee",
                "iqac",
                "last_year_committee_updates",
                "renewal_justification",
                "evidence",
                # Legacy fields (preserved for backward compatibility)
                "anti_ragging_committee",
                "icc_committee",
                "grievance_committee",
                "scst_cell",
                "last_updated_year",
            ]
        }
    },
    "ugc": {
        "faculty_and_staffing": {
            "required_fields": ["faculty_count"],
            "optional_fields": [
                "qualification_breakdown",
                "designation_breakdown",
                "faculty_onboarding_plan",
                "last_updated_year"
            ]
        },
        "student_enrollment_and_programs": {
            "required_fields": ["student_count"],
            "optional_fields": [
                "program_wise_enrollment",
                "proposed_programs",
                "last_updated_year",
                "last_year_exam_results",
                "exam_system",
            ]
        },
        "infrastructure_and_land_building": {
            "required_fields": ["built_up_area"],
            "optional_fields": [
                "land_area",
                "library_area",
                "land_ownership",
                "campus_details",
                "updated_facilities",
                "last_updated_year"
            ]
        },
        "academic_governance_and_bodies": {
            "required_fields": ["board_of_governors", "academic_council"],
            "optional_fields": [
                "finance_committee",
                "governance_structure",
                "trust_act_document",
                "last_year_governance_compliance",
                "last_year_committee_reports",
                "affiliation_request",
                "vision_mission",
                "last_updated_year"
            ]
        },
        "financial_information": {
            "required_fields": ["annual_budget"],
            "optional_fields": [
                "revenue",
                "expenditure",
                "budget_plan",
                "last_updated_year"
            ]
        },
        "research_and_publications": {
            "required_fields": ["publications"],
            "optional_fields": [
                "citations",
                "funded_projects",
                "last_year_research_data",
                "last_updated_year"
            ]
        },
        "iqac_quality_assurance": {
            "required_fields": ["iqac_established"],
            "optional_fields": ["accreditation_status", "last_updated_year"]
        },
        "learning_resources_library_ict": {
            "required_fields": ["library_area"],
            "optional_fields": ["ict_facilities", "last_updated_year"]
        },
        "regulatory_compliance": {
            "required_fields": ["ugc_regulations_2018_compliance"],
            "optional_fields": [
                "statutory_committees",
                "affiliation_request",
                "last_updated_year"
            ]
        },
        "future_academic_plan": {
            "required_fields": [],
            "optional_fields": [
                "expansion_plan",
                "new_programs",
                "strategic_vision",
                "proposed_programs",
                "last_updated_year"
            ]
        }
    }
}

def get_information_blocks(mode: str = None, new_university: bool = False) -> List[str]:
    """
    Get list of information blocks for a specific mode.
    If mode is None, returns AICTE blocks (default).
    
    For UGC mode:
    - If new_university=True: includes future_academic_plan (10 blocks)
    - If new_university=False (renewal): excludes future_academic_plan (9 blocks)
    """
    if mode is None:
        return AICTE_BLOCKS.copy()
    
    mode_lower = mode.lower()
    if mode_lower == "aicte":
        return AICTE_BLOCKS.copy()
    elif mode_lower == "ugc":
        blocks = UGC_BLOCKS.copy()
        # Only include future_academic_plan for new universities
        if not new_university:
            blocks = [b for b in blocks if b != "future_academic_plan"]
        return blocks
    else:
        # Default to AICTE for unknown modes
        return AICTE_BLOCKS.copy()

def get_block_description(block_id: str) -> Dict[str, Any]:
    """Get description and keywords for a block"""
    return BLOCK_DESCRIPTIONS.get(block_id, {})

def get_block_fields(block_id: str, mode: str) -> Dict[str, List[str]]:
    """Get required and optional fields for a block in a specific mode"""
    mode_blocks = BLOCK_FIELDS.get(mode.lower(), {})
    return mode_blocks.get(block_id, {"required_fields": [], "optional_fields": []})

def get_all_block_fields(mode: str) -> Dict[str, Dict[str, List[str]]]:
    """Get all block fields for a mode"""
    return BLOCK_FIELDS.get(mode.lower(), {})
