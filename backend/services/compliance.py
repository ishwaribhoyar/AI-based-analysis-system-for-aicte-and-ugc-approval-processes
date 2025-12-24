"""
Compliance and risk engine
Mode-specific compliance checks for AICTE and UGC
Uses fuzzy/synonym-aware matching for compliance certificates
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from config.rules import get_compliance_rules
from utils.parse_numeric import parse_numeric
try:
    from difflib import SequenceMatcher
except ImportError:
    SequenceMatcher = None

class ComplianceService:
    def check_compliance(
        self,
        mode: str,
        blocks: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check compliance rules and return flags based on information blocks
        Returns: List of {severity, title, reason, evidence, recommendation}
        """
        flags = []
        
        # Aggregate extracted data from blocks
        extracted_data = {}
        if blocks:
            # Aggregate from blocks (skip invalid blocks)
            for block in blocks:
                if block.get("is_invalid", False):
                    continue
                    
                data = block.get("extracted_data", {})
                if data:
                    for key, value in data.items():
                        if value is not None and value != "":
                            if key not in extracted_data or not extracted_data[key]:
                                extracted_data[key] = value
                            elif isinstance(value, (int, float)) and isinstance(extracted_data.get(key), (int, float)):
                                extracted_data[key] = max(extracted_data[key], value)
        
        # Run mode-specific compliance checks
        if mode.lower() == "aicte":
            flags.extend(self._check_aicte_compliance(blocks, extracted_data, mode))
        elif mode.lower() == "ugc":
            flags.extend(self._check_ugc_compliance(blocks, extracted_data, mode))
        
        return flags
    
    def _fuzzy_match(self, text: str, synonyms: List[str], threshold: float = 0.75) -> bool:
        """
        Check if text matches any synonym using fuzzy matching.
        Uses SequenceMatcher for similarity or simple substring matching.
        """
        if not text or not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        
        # First try exact substring match (case-insensitive)
        for synonym in synonyms:
            if synonym.lower() in text_lower or text_lower in synonym.lower():
                return True
        
        # Then try fuzzy similarity if SequenceMatcher available
        if SequenceMatcher:
            for synonym in synonyms:
                ratio = SequenceMatcher(None, text_lower, synonym.lower()).ratio()
                if ratio >= threshold:
                    return True
        
        # Fallback: token overlap
        text_tokens = set(text_lower.split())
        for synonym in synonyms:
            synonym_tokens = set(synonym.lower().split())
            if len(text_tokens & synonym_tokens) >= 2:  # At least 2 common words
                return True
        
        return False
    
    def _check_certificate_presence(self, blocks: List[Dict], certificate_synonyms: List[str], 
                                   block_type: str = None) -> tuple:
        """
        Check if certificate is present using fuzzy matching on evidence snippets.
        Returns (found: bool, evidence_snippet: str)
        """
        for block in blocks:
            if block_type and block.get("block_type") != block_type:
                continue
            
            extracted_data = block.get("extracted_data", {})
            evidence_snippet = block.get("evidence_snippet") or ""
            
            # Check in extracted_data boolean fields
            for key, value in extracted_data.items():
                if isinstance(value, bool) and value is True:
                    if self._fuzzy_match(key, certificate_synonyms):
                        return True, evidence_snippet or f"Found in {key}"
            
            # Check in evidence snippet text
            if evidence_snippet and self._fuzzy_match(evidence_snippet, certificate_synonyms):
                return True, evidence_snippet
            
            # Check field names
            for key in extracted_data.keys():
                if self._fuzzy_match(key, certificate_synonyms):
                    value = extracted_data[key]
                    if value is True or (isinstance(value, str) and value.lower() not in ["none", "null", "n/a"]):
                        return True, evidence_snippet or f"Found in {key}"
        
        return False, ""
    
    def _check_aicte_compliance(self, blocks: List[Dict], data: Dict, mode: str) -> List[Dict[str, Any]]:
        """AICTE-specific compliance checks with fuzzy matching"""
        flags = []
        
        # 1. Fire NOC validity (fuzzy matching)
        fire_noc_synonyms = [
            "Fire NOC", "Fire Safety NOC", "Fire Safety Certificate", 
            "Fire NOC certificate", "Fire clearance", "Fire safety clearance"
        ]
        fire_found, fire_evidence = self._check_certificate_presence(blocks, fire_noc_synonyms, 
                                                                      "safety_compliance_information")
        
        # Also check in aggregated data
        if not fire_found:
            for key in data.keys():
                if self._fuzzy_match(key, fire_noc_synonyms):
                    if data.get(key) is True:
                        fire_found = True
                        break
        
        if not fire_found:
            flags.append({
                "severity": "high",
                "title": "Missing or Invalid Fire NOC",
                "reason": "Fire NOC certificate is missing or not valid for current year",
                "recommendation": "Obtain valid Fire NOC certificate for current year"
            })
        
        # 2. Building Stability Certificate (fuzzy matching)
        building_synonyms = [
            "Building Structural Safety Certificate", "Building Stability Certificate",
            "Structural Safety Certificate", "Building Safety Certificate", "Structural Certificate"
        ]
        building_found, building_evidence = self._check_certificate_presence(blocks, building_synonyms,
                                                                            "safety_compliance_information")
        
        if not building_found:
            for key in data.keys():
                if self._fuzzy_match(key, building_synonyms):
                    if data.get(key) is True:
                        building_found = True
                        break
        
        if not building_found:
            flags.append({
                "severity": "high",
                "title": "Missing Building Stability Certificate",
                "reason": "Building Stability Certificate is missing",
                "recommendation": "Submit Building Stability Certificate"
            })
        
        # 3. Sanitary Certificate (fuzzy matching) - Only flag if mentioned AND expired
        sanitary_synonyms = [
            "Sanitary Certificate", "Environmental Clearance", 
            "Sanitary Certificate or Environmental Clearance", "Environmental Certificate"
        ]
        sanitary_found, sanitary_evidence = self._check_certificate_presence(blocks, sanitary_synonyms,
                                                                             "safety_compliance_information")
        
        if not sanitary_found:
            for key in data.keys():
                if self._fuzzy_match(key, sanitary_synonyms):
                    if data.get(key) is True:
                        sanitary_found = True
                        break
        
        # Check if sanitary certificate is mentioned in text
        sanitary_mentioned = False
        for block in blocks:
            if block.get("block_type") == "safety_compliance_information":
                extracted_data = block.get("extracted_data", {})
                evidence_snippet = block.get("evidence_snippet", "")
                text = (evidence_snippet + " " + str(extracted_data)).lower()
                if "sanitary" in text or "environmental clearance" in text:
                    sanitary_mentioned = True
                    # Check if expired (if date information available)
                    # For now, only flag if mentioned AND we can determine it's expired
                    # Since we don't have expiry date parsing, we'll only flag if explicitly mentioned as expired
                    if "expired" in text or "invalid" in text or "not valid" in text:
                        flags.append({
                            "severity": "low",  # Sanitary certificate missing → LOW severity
                            "title": "Sanitary Certificate Expired",
                            "reason": "Sanitary Certificate or Environmental Clearance is expired or invalid",
                            "recommendation": "Renew Sanitary Certificate"
                        })
                    break
        
        # Only flag as missing if it was mentioned but not found (not mandatory for all institutions)
        # Do NOT auto-flag if not mentioned at all
        
        # 4. Mandatory committees (ICC, SC/ST, Anti-ragging) - fuzzy matching
        committees_block = next((b for b in blocks if b.get("block_type") == "mandatory_committees_information"), None)
        if committees_block:
            committees_data = committees_block.get("extracted_data", {})
            evidence_snippet = committees_block.get("evidence_snippet", "")
            missing_committees = []
            
            # ICC committee synonyms
            icc_synonyms = ["ICC", "Internal Complaints Committee", "Internal Complaint Committee", 
                          "ICC Committee", "Internal Complaints"]
            icc_found = False
            for key in committees_data.keys():
                if self._fuzzy_match(key, icc_synonyms):
                    if committees_data.get(key) is True:
                        icc_found = True
                        break
            if evidence_snippet and self._fuzzy_match(evidence_snippet, icc_synonyms):
                icc_found = True
            if not icc_found:
                missing_committees.append("ICC (Internal Complaints Committee)")
            
            # Anti-ragging committee synonyms
            anti_ragging_synonyms = ["Anti-Ragging Committee", "Anti Ragging Committee", 
                                    "Anti-Ragging", "Anti Ragging", "Ragging Prevention Committee"]
            anti_ragging_found = False
            for key in committees_data.keys():
                if self._fuzzy_match(key, anti_ragging_synonyms):
                    if committees_data.get(key) is True:
                        anti_ragging_found = True
                        break
            if evidence_snippet and self._fuzzy_match(evidence_snippet, anti_ragging_synonyms):
                anti_ragging_found = True
            if not anti_ragging_found:
                missing_committees.append("Anti-Ragging Committee")
            
            if missing_committees:
                flags.append({
                    "severity": "high",
                    "title": "Missing Mandatory Committees",
                    "reason": f"Required committees not found: {', '.join(missing_committees)}",
                    "recommendation": "Establish and document all mandatory committees"
                })
        
        # 5. Approved faculty appointment letters (check in faculty block)
        faculty_block = next((b for b in blocks if b.get("block_type") == "faculty_information"), None)
        if faculty_block:
            faculty_data = faculty_block.get("extracted_data", {})
            total_faculty = parse_numeric(faculty_data.get("total_faculty")) or parse_numeric(faculty_data.get("faculty_count"))
            if total_faculty and total_faculty > 0:
                # Check if appointment letters are mentioned (basic check)
                # In real implementation, this would check for explicit evidence
                pass  # Placeholder - would need more detailed extraction
        
        # 6. Land ownership / Lease documents (check in infrastructure block)
        infra_block = next((b for b in blocks if b.get("block_type") == "infrastructure_information"), None)
        if infra_block:
            infra_data = infra_block.get("extracted_data", {})
            # Check for land ownership/lease mention
            # In real implementation, this would check for explicit evidence
            pass  # Placeholder - would need more detailed extraction
        
        # 7. Affidavit (general check - would need explicit extraction)
        # Placeholder - would need more detailed extraction
        
        return flags
    
    def _check_ugc_compliance(self, blocks: List[Dict], data: Dict, mode: str) -> List[Dict[str, Any]]:
        """UGC-specific compliance checks"""
        flags = []
        
        # 1. Governance bodies (BoG, AC, FC, IQAC)
        governance_block = next((b for b in blocks if b.get("block_type") == "academic_governance_and_bodies"), None)
        if governance_block:
            gov_data = governance_block.get("extracted_data", {})
            missing_bodies = []
            
            if not gov_data.get("board_of_governors"):
                missing_bodies.append("Board of Governors (BoG)")
            if not gov_data.get("academic_council"):
                missing_bodies.append("Academic Council (AC)")
            if not gov_data.get("finance_committee"):
                missing_bodies.append("Finance Committee (FC)")
            
            if missing_bodies:
                flags.append({
                    "severity": "high",
                    "title": "Missing Governance Bodies",
                    "reason": f"Required governance bodies not found: {', '.join(missing_bodies)}",
                    "recommendation": "Establish and document all required governance bodies"
                })
        
        # Check IQAC separately
        iqac_block = next((b for b in blocks if b.get("block_type") == "iqac_quality_assurance"), None)
        if iqac_block:
            iqac_data = iqac_block.get("extracted_data", {})
            if not iqac_data.get("iqac_established"):
                flags.append({
                    "severity": "high",
                    "title": "IQAC Not Established",
                    "reason": "Internal Quality Assurance Cell (IQAC) is not established",
                    "recommendation": "Establish IQAC as per UGC guidelines"
                })
        
        # 2. UGC Regulations 2018 compliance
        compliance_block = next((b for b in blocks if b.get("block_type") == "regulatory_compliance"), None)
        if compliance_block:
            compliance_data = compliance_block.get("extracted_data", {})
            if not compliance_data.get("ugc_regulations_2018_compliance"):
                flags.append({
                    "severity": "high",
                    "title": "UGC Regulations 2018 Non-Compliance",
                    "reason": "UGC Regulations 2018 compliance not confirmed",
                    "recommendation": "Ensure full compliance with UGC Regulations 2018"
                })
        
        # 3. Financial viability (check in financial_information block)
        financial_block = next((b for b in blocks if b.get("block_type") == "financial_information"), None)
        if financial_block:
            financial_data = financial_block.get("extracted_data", {})
            annual_budget = parse_numeric(financial_data.get("annual_budget"))
            if annual_budget is None:
                flags.append({
                    "severity": "medium",
                    "title": "Financial Information Missing",
                    "reason": "Annual budget information is missing",
                    "recommendation": "Submit complete financial information demonstrating viability"
                })
        
        # 4. Statutory committees (check in regulatory_compliance block)
        if compliance_block:
            compliance_data = compliance_block.get("extracted_data", {})
            statutory_committees = compliance_data.get("statutory_committees")
            if not statutory_committees:
                flags.append({
                    "severity": "medium",
                    "title": "Statutory Committees Missing",
                    "reason": "Statutory committees information is missing",
                    "recommendation": "Document all statutory committees"
                })
        
        # 5. Mandatory disclosures (check in regulatory_compliance block)
        if compliance_block:
            compliance_data = compliance_block.get("extracted_data", {})
            # In real implementation, would check for explicit disclosure evidence
            pass  # Placeholder
        
        # 6. Affidavit (general check - would need explicit extraction)
        # Placeholder - would need more detailed extraction
        
        return flags
