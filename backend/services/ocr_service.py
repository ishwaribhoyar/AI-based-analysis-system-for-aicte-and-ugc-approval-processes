"""
PaddleOCR Fallback Service
Only used when Docling returns empty text for pages
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not installed. Install with: pip install paddleocr")

class OCRService:
    """PaddleOCR fallback service for pages with no text"""
    
    def __init__(self):
        if not PADDLEOCR_AVAILABLE:
            logger.warning("PaddleOCR not available. OCR fallback will not work.")
            self.ocr = None
        else:
            try:
                # Initialize PaddleOCR (use_angle_cls=True for better accuracy)
                # Try without show_log first (newer versions don't support it)
                try:
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                except TypeError:
                    # Fallback for versions that don't support show_log
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
                logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                self.ocr = None
    
    def ocr_page(self, image_path: str) -> str:
        """
        Run OCR on a single page image
        Returns: Extracted text
        """
        if not self.ocr:
            return ""
        
        try:
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return ""
            
            # Extract text from OCR results
            text_lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    if text:
                        text_lines.append(text)
            
            return "\n".join(text_lines)
            
        except Exception as e:
            logger.error(f"OCR error for {image_path}: {e}")
            return ""
    
    def ocr_pdf_pages(self, pdf_path: str, page_numbers: List[int]) -> Dict[int, str]:
        """
        Run OCR on specific pages of a PDF
        Returns: Dict mapping page number to extracted text
        """
        if not self.ocr:
            return {}
        
        try:
            # Convert PDF pages to images
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, first_page=min(page_numbers), last_page=max(page_numbers))
            
            ocr_results = {}
            for idx, page_num in enumerate(page_numbers):
                if idx < len(images):
                    # Save temporary image
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        images[idx].save(tmp.name)
                        text = self.ocr_page(tmp.name)
                        ocr_results[page_num] = text
                        # Clean up
                        Path(tmp.name).unlink()
            
            return ocr_results
            
        except ImportError:
            logger.warning("pdf2image not installed. Cannot convert PDF pages to images.")
            return {}
        except Exception as e:
            logger.error(f"PDF OCR error: {e}")
            return {}

