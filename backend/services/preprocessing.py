"""
DEPRECATED: Document preprocessing using Unstructured-IO
This service has been replaced by DoclingService + OCRService
Kept for backward compatibility only - DO NOT USE IN NEW CODE
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Unstructured-IO imports
# Note: These imports work at runtime but may show linter warnings
# The package is installed in the virtual environment
try:
    from unstructured.partition.auto import partition  # type: ignore[import-untyped]
    from unstructured.staging.base import elements_to_json  # type: ignore[import-untyped]
except ImportError:
    # Fallback imports if package structure changes
    try:
        from unstructured.partition import auto  # type: ignore[import-untyped]
        partition = auto.partition
        from unstructured.staging import base  # type: ignore[import-untyped]
        elements_to_json = base.elements_to_json
    except ImportError as e:
        raise ImportError(
            "unstructured package not found. Please install it with: "
            "pip install 'unstructured[local-inference]'"
        ) from e

logger = logging.getLogger(__name__)

class PreprocessingService:
    def __init__(self):
        self.local_mode = True  # Using local Unstructured-IO
    
    def preprocess_document(
        self,
        file_path: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """
        Preprocess document using Unstructured-IO
        Returns: {
            elements: [...],
            text: "...",
            page_images: [...]
        }
        """
        try:
            # Determine strategy
            strategy = self._determine_strategy(file_path, mime_type)
            
            # Partition document
            elements = partition(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                extract_images_in_pdf=True
            )
            
            # Convert to JSON-serializable format
            elements_json_str = elements_to_json(elements)
            # Parse JSON string to list of dicts if it's a string
            try:
                if isinstance(elements_json_str, str):
                    elements_json = json.loads(elements_json_str)
                else:
                    elements_json = elements_json_str
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, create a simple structure from elements
                logger.warning(f"Failed to parse elements JSON, creating fallback structure: {e}")
                elements_json = []
                for elem in elements:
                    if hasattr(elem, 'text'):
                        elements_json.append({"text": elem.text, "type": type(elem).__name__})
                    else:
                        elements_json.append({"text": str(elem), "type": type(elem).__name__})
            
            # Extract full text - properly handle both element objects and JSON
            text_parts = []
            for elem in elements:
                if hasattr(elem, 'text'):
                    text_parts.append(elem.text)
                elif hasattr(elem, '__str__'):
                    text_parts.append(str(elem))
                else:
                    text_parts.append(str(elem))
            
            full_text = "\n\n".join([t for t in text_parts if t and t.strip()])
            
            # Generate page images (simplified - in production use pdf2image)
            page_images = self._generate_page_images(file_path)
            
            return {
                "elements": elements_json,
                "text": full_text,
                "page_images": page_images,
                "element_count": len(elements)
            }
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            raise
    
    def _determine_strategy(self, file_path: str, mime_type: str) -> str:
        """Determine Unstructured-IO strategy"""
        if "pdf" in mime_type.lower():
            return "hi_res"  # High resolution for PDFs
        elif "image" in mime_type.lower():
            return "ocr_only"  # OCR for images
        else:
            return "auto"  # Auto-detect
    
    def _generate_page_images(self, file_path: str) -> List[str]:
        """Generate page images for evidence (simplified)"""
        # In production, use pdf2image or similar
        # For now, return empty list
        return []

