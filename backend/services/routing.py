"""
Routing engine - determines processing strategy before AI calls
"""

from typing import Dict, Any
import os
from pathlib import Path
from utils.file_utils import is_image_file, get_mime_type

class RoutingService:
    def create_processing_plan(
        self,
        file_path: str,
        filename: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """
        Create processing plan for document
        Returns: {
            needs_ocr: bool,
            is_scanned: bool,
            is_encrypted: bool,
            extraction_strategy: str,
            should_chunk: bool,
            possible_doc_types: List[str]
        }
        """
        # Check if OCR needed
        needs_ocr = is_image_file(filename) or self._is_likely_scanned(file_path, mime_type)
        
        # Check if encrypted (simplified - try to read)
        is_encrypted = self._check_encryption(file_path)
        
        # Determine extraction strategy
        extraction_strategy = self._determine_extraction_strategy(mime_type, filename)
        
        # Should chunk?
        file_size = os.path.getsize(file_path)
        should_chunk = file_size > 5 * 1024 * 1024  # 5MB threshold
        
        # Possible doc types (based on filename heuristics)
        possible_doc_types = self._guess_doc_types(filename)
        
        return {
            "needs_ocr": needs_ocr,
            "is_scanned": needs_ocr,
            "is_encrypted": is_encrypted,
            "extraction_strategy": extraction_strategy,
            "should_chunk": should_chunk,
            "possible_doc_types": possible_doc_types,
            "file_size": file_size
        }
    
    def _is_likely_scanned(self, file_path: str, mime_type: str) -> bool:
        """Heuristic to detect scanned documents"""
        # Simplified - in production use OCR confidence
        return "image" in mime_type.lower()
    
    def _check_encryption(self, file_path: str) -> bool:
        """Check if PDF is encrypted (simplified)"""
        try:
            if file_path.endswith('.pdf'):
                # Try to read first page
                with open(file_path, 'rb') as f:
                    content = f.read(1024)
                    # Simple check for encryption markers
                    return b'/Encrypt' in content
            return False
        except:
            return True  # Assume encrypted if can't check
    
    def _determine_extraction_strategy(self, mime_type: str, filename: str) -> str:
        """Determine extraction strategy"""
        if "spreadsheet" in mime_type.lower() or filename.endswith(('.xlsx', '.xls')):
            return "table_focused"
        elif "presentation" in mime_type.lower() or filename.endswith(('.pptx', '.ppt')):
            return "slide_focused"
        else:
            return "general"
    
    def _guess_doc_types(self, filename: str) -> list[str]:
        """Guess possible document types from filename"""
        filename_lower = filename.lower()
        guesses = []
        
        if "faculty" in filename_lower:
            guesses.append("faculty_list")
        if "infrastructure" in filename_lower or "infra" in filename_lower:
            guesses.append("infrastructure_report")
        if "placement" in filename_lower:
            guesses.append("placement_report")
        if "fire" in filename_lower or "noc" in filename_lower:
            guesses.append("fire_noc")
        if "research" in filename_lower or "publication" in filename_lower:
            guesses.append("research_publications")
        if "fee" in filename_lower:
            guesses.append("fee_structure")
        if "lab" in filename_lower or "equipment" in filename_lower:
            guesses.append("lab_equipment_list")
        if "calendar" in filename_lower or "academic" in filename_lower:
            guesses.append("academic_calendar")
        
        return guesses if guesses else ["unknown"]

