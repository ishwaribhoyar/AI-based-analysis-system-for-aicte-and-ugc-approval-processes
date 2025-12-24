"""
Mode-specific rules and configurations for UGC and AICTE
"""

from typing import Dict, List

# DEPRECATED: Document types removed
# System now uses 10 Information Blocks only
# See config/information_blocks.py for block definitions

# KPI definitions and formulas
KPI_FORMULAS = {
    "ugc": {
        "research_index": {
            "name": "Research Index",
            "formula": "calculate_research_index",
            "weight": 0.3
        },
        "governance_score": {
            "name": "Governance Score",
            "formula": "calculate_governance_score",
            "weight": 0.3
        },
        "student_outcome_index": {
            "name": "Student Outcome Index",
            "formula": "calculate_student_outcome_index",
            "weight": 0.4
        }
    },
    "aicte": {
        "fsr_score": {
            "name": "FSR Score",
            "formula": "calculate_fsr_score",
            "weight": 0.25
        },
        "infrastructure_score": {
            "name": "Infrastructure Score",
            "formula": "calculate_infrastructure_score",
            "weight": 0.25
        },
        "placement_index": {
            "name": "Placement Index",
            "formula": "calculate_placement_index",
            "weight": 0.25
        },
        "lab_compliance_index": {
            "name": "Lab Compliance Index",
            "formula": "calculate_lab_compliance_index",
            "weight": 0.25
        }
    }
}

# Compliance rules
COMPLIANCE_RULES = {
    "ugc": [
        {
            "rule_id": "missing_committees",
            "severity": "high",
            "check": "check_missing_committees"
        },
        {
            "rule_id": "expired_accreditation",
            "severity": "high",
            "check": "check_expired_accreditation"
        },
        {
            "rule_id": "insufficient_research",
            "severity": "medium",
            "check": "check_research_output"
        }
    ],
    "aicte": [
        {
            "rule_id": "expired_fire_noc",
            "severity": "high",
            "check": "check_fire_noc_expiry"
        },
        {
            "rule_id": "missing_approvals",
            "severity": "high",
            "check": "check_missing_approvals"
        },
        {
            "rule_id": "low_fsr",
            "severity": "medium",
            "check": "check_fsr_ratio"
        },
        {
            "rule_id": "placement_issues",
            "severity": "medium",
            "check": "check_placement_data"
        }
    ]
}

# DEPRECATED: Document-based functions removed
# Use get_information_blocks() from config.information_blocks instead

def get_kpi_formulas(mode: str) -> Dict:
    """Get KPI formulas for mode"""
    return KPI_FORMULAS.get(mode.lower(), {})

def get_compliance_rules(mode: str) -> List[Dict]:
    """Get compliance rules for mode"""
    return COMPLIANCE_RULES.get(mode.lower(), [])

