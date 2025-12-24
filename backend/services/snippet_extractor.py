"""
Block Snippet Extraction Service
Quick keyword-based filtering before LLM extraction.
"""

from typing import Dict, List
from config.information_blocks import get_information_blocks, get_block_description


DEFAULT_KEYWORDS = {
    "faculty_information": [
        "faculty", "professor", "associate", "assistant", "teaching",
        "non-teaching", "phd", "qualification", "department"
    ],
    "student_enrollment_information": [
        "enrollment", "intake", "admitted", "strength", "sanctioned",
        "boys", "girls", "total students"
    ],
    "infrastructure_information": [
        "classroom", "lab", "built-up", "area", "infrastructure",
        "equipment", "facility", "workshop", "auditorium"
    ],
    "lab_equipment_information": [
        "lab", "laboratory", "equipment", "experiment", "instruments", "workstation"
    ],
    "safety_compliance_information": [
        "fire", "safety", "noc", "certificate", "compliance", "approval",
        "renewal", "validity"
    ],
    "academic_calendar_information": [
        "semester", "calendar", "schedule", "timeline", "week", "session",
        "midterm", "vacation", "exam"
    ],
    "fee_structure_information": [
        "fee", "tuition", "hostel fee", "development fee", "exam fee",
        "scholarship", "payment"
    ],
    "placement_information": [
        "placement", "offer", "salary", "median", "package", "recruiter",
        "campus", "internship"
    ],
    "research_innovation_information": [
        "research", "publication", "journal", "conference", "patent",
        "citation", "grant", "project"
    ],
    "mandatory_committees_information": [
        "committee", "anti ragging", "iqac", "disciplinary",
        "complaint", "grievance", "admission", "internal complaint"
    ],
}


class SnippetExtractor:
    """Keyword-based snippet extraction for each information block."""

    def __init__(self, max_lines: int = 20):
        self.max_lines = max_lines
        self.block_ids = get_information_blocks()

    def extract_snippets(self, full_text: str) -> Dict[str, str]:
        """Return relevant snippets for each block."""
        cleaned_lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        snippets: Dict[str, str] = {}

        for block_id in self.block_ids:
            keywords = self._get_keywords(block_id)
            matched = self._match_lines(cleaned_lines, keywords)

            if not matched:
                # Fallback: use block name keywords or description
                fallback_kw = get_block_description(block_id).get("keywords", [])
                matched = self._match_lines(cleaned_lines, fallback_kw)

            snippets[block_id] = "\n".join(matched[: self.max_lines])

        return snippets

    def _get_keywords(self, block_id: str) -> List[str]:
        return DEFAULT_KEYWORDS.get(block_id, [])

    def _match_lines(self, lines: List[str], keywords: List[str]) -> List[str]:
        if not keywords:
            return []
        keywords_lower = [kw.lower() for kw in keywords if kw]
        matched = []
        for line in lines:
            lower_line = line.lower()
            if any(kw in lower_line for kw in keywords_lower):
                matched.append(line)
        return matched


