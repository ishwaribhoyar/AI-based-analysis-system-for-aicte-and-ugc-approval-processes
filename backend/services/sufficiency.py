"""
DEPRECATED: Document sufficiency scoring engine
This service is kept for backward compatibility but is no longer used.
The system now uses BlockSufficiencyService for information block sufficiency calculation.
"""

from typing import Dict, Any, List
from config.rules import get_required_documents

class SufficiencyService:
    def calculate_sufficiency(
        self,
        mode: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate document sufficiency
        Formula: base_pct = (P/R)*100
                 penalty = D*2 + O*4 + L*5 + I*7
                 penalty = min(penalty, 50)
                 sufficiency = max(0, base_pct - penalty)
        """
        required = get_required_documents(mode)
        present_doc_types = set()
        
        # Count present documents
        for doc in documents:
            doc_type = doc.get("doc_type")
            filename = doc.get("filename", "").lower()
            
            # If doc_type is unknown, try to infer from filename
            if not doc_type or doc_type == "unknown":
                doc_type = self._infer_doc_type_from_filename(filename, mode)
            
            if doc_type and doc_type != "unknown":
                # Check exact match first
                if doc_type in required:
                    present_doc_types.add(doc_type)
                else:
                    # Check for partial matches (e.g., "approval_letters" might contain info about multiple doc types)
                    # Also check if doc_type contains any required type or vice versa
                    for req_type in required:
                        if req_type in doc_type or doc_type in req_type:
                            present_doc_types.add(req_type)
                            break
                    # Special handling: approval_letters might contain fire_noc, safety_certificates info
                    if doc_type == "approval_letters":
                        # Check if document contains keywords that suggest it has required document info
                        extracted_data = doc.get("extracted_data", {})
                        text = doc.get("extracted_text", "") or str(extracted_data)
                        text_lower = text.lower()
                        # Map approval_letters content to required documents
                        if "fire" in text_lower or "noc" in text_lower:
                            present_doc_types.add("fire_noc")
                        if "safety" in text_lower or "certificate" in text_lower:
                            present_doc_types.add("safety_certificates")
                        if "faculty" in text_lower or "staff" in text_lower:
                            present_doc_types.add("faculty_list")
                        if "infrastructure" in text_lower or "building" in text_lower or "area" in text_lower:
                            present_doc_types.add("infrastructure_report")
            else:
                # Even if doc_type is unknown, try to match from filename directly
                for req_type in required:
                    if self._filename_matches_type(filename, req_type):
                        present_doc_types.add(req_type)
                        break
        
        P = len(present_doc_types)
        R = len(required)
        
        # Calculate base percentage
        base_pct = (P / R * 100) if R > 0 else 0
        
        # Count penalties
        D = sum(1 for doc in documents if "duplicate" in doc.get("quality_flags", []))
        O = sum(1 for doc in documents if "outdated" in doc.get("quality_flags", []))
        L = sum(1 for doc in documents if "low_quality" in doc.get("quality_flags", []))
        I = sum(1 for doc in documents if "invalid" in doc.get("quality_flags", []))
        
        # Calculate penalty
        penalty = D * 2 + O * 4 + L * 5 + I * 7
        penalty = min(penalty, 50)
        
        # Final sufficiency
        sufficiency = max(0, base_pct - penalty)
        
        # Missing documents
        missing = [doc_type for doc_type in required if doc_type not in present_doc_types]
        
        # Determine color
        if sufficiency >= 80:
            color = "green"
        elif sufficiency >= 60:
            color = "yellow"
        else:
            color = "red"
        
        return {
            "percentage": round(sufficiency, 2),
            "present_count": P,
            "required_count": R,
            "missing_documents": missing,
            "penalty_breakdown": {
                "duplicate": D,
                "outdated": O,
                "low_quality": L,
                "invalid": I
            },
            "penalty_points": penalty,
            "color": color
        }
    
    def _infer_doc_type_from_filename(self, filename: str, mode: str) -> str:
        """Infer document type from filename using keyword matching"""
        if not filename:
            return "unknown"
        
        filename_lower = filename.lower()
        from config.rules import get_document_types
        available_types = get_document_types(mode)
        
        # Keyword mapping
        keyword_map = {
            "academic_calendar": ["calendar", "academic calendar", "academic_calendar", "schedule", "academic year"],
            "faculty_list": ["faculty", "staff", "teacher", "professor", "faculty list"],
            "infrastructure_report": ["infrastructure", "building", "campus", "facility", "infrastructure report"],
            "placement_report": ["placement", "job", "career", "placement report", "recruitment"],
            "lab_equipment_list": ["lab", "laboratory", "equipment", "lab equipment", "instruments"],
            "fire_noc": ["fire", "noc", "fire noc", "fire safety", "fire certificate"],
            "fee_structure": ["fee", "fees", "fee structure", "tuition", "payment"],
            "safety_certificates": ["safety", "certificate", "safety certificate", "compliance"],
            "approval_letters": ["approval", "letter", "permit", "authorization", "approval letter"],
            "research_publications": ["research", "publication", "paper", "journal", "research paper"],
            "governance_documents": ["governance", "policy", "bylaw", "governance document"],
            "student_outcomes": ["outcome", "student outcome", "performance", "result", "achievement"],
            "financial_statements": ["financial", "budget", "statement", "financial statement", "expenditure"],
            "statutory_committees": ["committee", "statutory", "board", "council", "committee list"]
        }
        
        # Check for matches
        for doc_type, keywords in keyword_map.items():
            if doc_type in available_types:
                for keyword in keywords:
                    if keyword in filename_lower:
                        return doc_type
        
        return "unknown"
    
    def _filename_matches_type(self, filename: str, doc_type: str) -> bool:
        """Check if filename matches a document type"""
        if not filename:
            return False
        
        filename_lower = filename.lower()
        keyword_map = {
            "academic_calendar": ["calendar", "academic calendar", "academic_calendar", "schedule", "academic year"],
            "faculty_list": ["faculty", "staff", "teacher", "professor", "faculty list"],
            "infrastructure_report": ["infrastructure", "building", "campus", "facility", "infrastructure report"],
            "placement_report": ["placement", "job", "career", "placement report", "recruitment"],
            "lab_equipment_list": ["lab", "laboratory", "equipment", "lab equipment", "instruments"],
            "fire_noc": ["fire", "noc", "fire noc", "fire safety", "fire certificate"],
            "fee_structure": ["fee", "fees", "fee structure", "tuition", "payment"],
            "safety_certificates": ["safety", "certificate", "safety certificate", "compliance"],
            "approval_letters": ["approval", "letter", "permit", "authorization", "approval letter"],
            "research_publications": ["research", "publication", "paper", "journal", "research paper"],
            "governance_documents": ["governance", "policy", "bylaw", "governance document"],
            "student_outcomes": ["outcome", "student outcome", "performance", "result", "achievement"],
            "financial_statements": ["financial", "budget", "statement", "financial statement", "expenditure"],
            "statutory_committees": ["committee", "statutory", "board", "council", "committee list"]
        }
        
        keywords = keyword_map.get(doc_type, [])
        for keyword in keywords:
            if keyword in filename_lower:
                return True
        
        return False

