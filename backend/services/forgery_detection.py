"""
Document Forgery Detection Service.
Checks documents for signs of tampering, manipulation, or inauthenticity.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# Suspicious PDF producer names (commonly used for document manipulation)
SUSPICIOUS_PRODUCERS = [
    "ilovepdf", "sejda", "smallpdf", "pdf24", "pdfcandy",
    "online2pdf", "freepdfconvert", "combinepdf", "mergepdf",
    "pdfmerge", "unknown creator", "pdf editor", "pdf modifier",
    "adobe reader",  # Reader can't create, only view - suspicious if listed as producer
]

# Patterns that suggest AI-generated or templated content
SUSPICIOUS_PATTERNS = [
    r"\b(\d{3,})\b.*\b\1\b.*\b\1\b",  # Same number repeated 3+ times
    r"Lorem ipsum",  # Placeholder text
    r"XX+",  # Placeholder marks
    r"\[INSERT.*?\]",  # Template placeholders
    r"<.*?>",  # HTML tags in document
]


def check_pdf_metadata(file_path: str) -> Tuple[bool, List[str]]:
    """
    Check PDF metadata for anomalies.
    
    Returns: (is_suspicious, list of issues)
    """
    issues = []
    
    try:
        import pypdf
        
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            metadata = reader.metadata
            
            if not metadata:
                issues.append("No metadata found - potentially stripped")
                return len(issues) > 1, issues
            
            # Check creation vs modification date
            created = metadata.get('/CreationDate', '')
            modified = metadata.get('/ModDate', '')
            
            if created and modified:
                try:
                    # Parse PDF date format (D:YYYYMMDDHHmmSS)
                    created_dt = _parse_pdf_date(created)
                    modified_dt = _parse_pdf_date(modified)
                    
                    if created_dt and modified_dt:
                        if created_dt > modified_dt:
                            issues.append(f"Creation date ({created_dt}) > Modification date ({modified_dt})")
                except:
                    pass
            
            # Check producer
            producer = str(metadata.get('/Producer', '')).lower()
            for suspicious in SUSPICIOUS_PRODUCERS:
                if suspicious in producer:
                    issues.append(f"Suspicious PDF producer detected: {producer}")
                    break
            
            # Check creator
            creator = str(metadata.get('/Creator', '')).lower()
            if not creator or creator in ['', 'unknown', 'none']:
                issues.append("Missing/unknown document creator")
            
    except Exception as e:
        logger.warning(f"Error checking PDF metadata: {e}")
        issues.append(f"Could not read PDF metadata: {str(e)[:50]}")
    
    # More than 2 issues suggests forgery
    return len(issues) >= 2, issues


def _parse_pdf_date(date_str: str) -> datetime:
    """Parse PDF date format to datetime."""
    try:
        # Format: D:YYYYMMDDHHmmSS(+/-HH'mm')
        date_str = date_str.replace("D:", "").replace("'", "")
        if len(date_str) >= 14:
            return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
    except:
        pass
    return None


def check_text_anomalies(extracted_text: str) -> Tuple[bool, List[str]]:
    """
    Check extracted text for suspicious patterns.
    
    Returns: (is_suspicious, list of issues)
    """
    issues = []
    
    if not extracted_text:
        issues.append("No text extracted from document")
        return True, issues
    
    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, extracted_text, re.IGNORECASE)
        if matches:
            issues.append(f"Suspicious pattern found: {pattern[:30]}...")
    
    # Check for repeated numeric sequences (AI-generated noise)
    numbers = re.findall(r'\b\d{4,}\b', extracted_text)
    if numbers:
        from collections import Counter
        num_counts = Counter(numbers)
        for num, count in num_counts.most_common(5):
            if count > 5:
                issues.append(f"Number '{num}' repeated {count} times")
    
    # Check character distribution (too uniform = suspicious)
    if len(extracted_text) > 1000:
        char_counts = {}
        for char in extracted_text.lower():
            if char.isalpha():
                char_counts[char] = char_counts.get(char, 0) + 1
        
        if char_counts:
            values = list(char_counts.values())
            avg = sum(values) / len(values)
            variance = sum((x - avg) ** 2 for x in values) / len(values)
            
            # Very low variance suggests generated text
            if variance < 10 and len(values) > 20:
                issues.append("Suspiciously uniform character distribution")
    
    return len(issues) >= 2, issues


def check_text_ocr_mismatch(
    docling_text: str, 
    ocr_text: str, 
    threshold: float = 0.4
) -> Tuple[bool, str]:
    """
    Check if there's a significant mismatch between Docling text and OCR text.
    A large mismatch (>40%) suggests document manipulation.
    
    Returns: (is_suspicious, message)
    """
    if not docling_text or not ocr_text:
        return False, "Insufficient text for comparison"
    
    # Normalize texts
    docling_words = set(docling_text.lower().split())
    ocr_words = set(ocr_text.lower().split())
    
    if not docling_words or not ocr_words:
        return False, "No words extracted"
    
    # Calculate Jaccard similarity
    intersection = len(docling_words & ocr_words)
    union = len(docling_words | ocr_words)
    
    if union == 0:
        return False, "No words to compare"
    
    similarity = intersection / union
    mismatch = 1 - similarity
    
    if mismatch > threshold:
        return True, f"Text-to-OCR mismatch: {mismatch*100:.1f}% (threshold: {threshold*100:.0f}%)"
    
    return False, f"Text-to-OCR match: {similarity*100:.1f}%"


def check_font_anomalies(file_path: str) -> Tuple[bool, List[str]]:
    """
    Check for font substitution anomalies.
    Multiple incompatible fonts or missing font info can indicate manipulation.
    
    Returns: (is_suspicious, list of issues)
    """
    issues = []
    
    try:
        import pypdf
        
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            all_fonts = set()
            for page in reader.pages[:10]:  # Check first 10 pages
                if '/Font' in page.get('/Resources', {}):
                    fonts = page['/Resources']['/Font']
                    if fonts:
                        for font_key in fonts.keys():
                            font = fonts[font_key]
                            if hasattr(font, 'get'):
                                font_name = font.get('/BaseFont', str(font_key))
                                all_fonts.add(str(font_name))
            
            # Too many different fonts suggests copy-paste manipulation
            if len(all_fonts) > 15:
                issues.append(f"Excessive font variety: {len(all_fonts)} fonts detected")
            
            # Check for system fonts mixed with document fonts
            system_fonts = {'Arial', 'Times', 'Helvetica', 'Courier'}
            has_system = any(any(sf.lower() in f.lower() for sf in system_fonts) for f in all_fonts)
            non_system = [f for f in all_fonts if not any(sf.lower() in f.lower() for sf in system_fonts)]
            
            if has_system and len(non_system) > 5:
                issues.append("Mixed system and custom fonts (potential manipulation)")
                
    except Exception as e:
        logger.debug(f"Font check skipped: {e}")
    
    return len(issues) >= 1, issues


def forgery_check(file_path: str, extracted_text: str = None) -> Dict[str, Any]:
    """
    Main forgery detection function.
    Runs all checks and returns comprehensive result.
    
    Returns dict with:
    - is_forged: bool
    - confidence: float (0-1, how confident we are it's forged)
    - issues: list of detected issues
    - recommendation: str
    """
    all_issues = []
    checks_passed = 0
    checks_total = 0
    
    # 1. PDF Metadata check
    checks_total += 1
    is_sus_meta, meta_issues = check_pdf_metadata(file_path)
    if is_sus_meta:
        all_issues.extend(meta_issues)
    else:
        checks_passed += 1
    
    # 2. Text anomalies check
    if extracted_text:
        checks_total += 1
        is_sus_text, text_issues = check_text_anomalies(extracted_text)
        if is_sus_text:
            all_issues.extend(text_issues)
        else:
            checks_passed += 1
    
    # 3. Font anomalies check
    checks_total += 1
    is_sus_font, font_issues = check_font_anomalies(file_path)
    if is_sus_font:
        all_issues.extend(font_issues)
    else:
        checks_passed += 1
    
    # Calculate forgery confidence
    issue_count = len(all_issues)
    if issue_count == 0:
        confidence = 0.0
        is_forged = False
        recommendation = "Document appears authentic"
    elif issue_count <= 2:
        confidence = 0.3
        is_forged = False
        recommendation = "Minor anomalies detected, likely authentic"
    elif issue_count <= 4:
        confidence = 0.6
        is_forged = True
        recommendation = "Multiple issues detected, review manually"
    else:
        confidence = 0.85
        is_forged = True
        recommendation = "High probability of document manipulation"
    
    return {
        "is_forged": is_forged,
        "confidence": confidence,
        "issues": all_issues,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "recommendation": recommendation,
    }


def validate_document_for_processing(
    file_path: str,
    extracted_text: str,
    extracted_blocks_count: int,
    llm_confidence: float = 0.5,
) -> Dict[str, Any]:
    """
    Comprehensive document validation before processing.
    Combines forgery detection with quality checks.
    
    Returns dict with:
    - is_valid: bool
    - reason: str (if invalid)
    - forgery_result: dict (forgery check results)
    """
    # Run forgery check
    forgery_result = forgery_check(file_path, extracted_text)
    
    # Check if forged
    if forgery_result["is_forged"] and forgery_result["confidence"] >= 0.6:
        return {
            "is_valid": False,
            "reason": f"Document appears forged: {forgery_result['recommendation']}",
            "forgery_result": forgery_result,
        }
    
    # Check minimum blocks
    if extracted_blocks_count < 5:
        return {
            "is_valid": False,
            "reason": f"Insufficient blocks extracted: {extracted_blocks_count} < 5",
            "forgery_result": forgery_result,
        }
    
    # Check text length
    if len(extracted_text or "") < 1000:
        return {
            "is_valid": False,
            "reason": f"Document text too short: {len(extracted_text or '')} < 1000 chars",
            "forgery_result": forgery_result,
        }
    
    # Check LLM confidence
    if llm_confidence < 0.35:
        return {
            "is_valid": False,
            "reason": f"Extraction confidence too low: {llm_confidence:.2f} < 0.35",
            "forgery_result": forgery_result,
        }
    
    return {
        "is_valid": True,
        "reason": "Document passed all validation checks",
        "forgery_result": forgery_result,
    }
