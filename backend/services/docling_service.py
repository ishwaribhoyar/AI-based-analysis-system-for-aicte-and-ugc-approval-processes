"""
Docling Document Parsing Service
Primary extraction engine - replaces Unstructured-IO
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import json

logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not installed. Please install with: pip install docling")

class DoclingService:
    """Docling-based document parsing service with fallback"""
    
    def __init__(self):
        self.docling_available = DOCLING_AVAILABLE
        
        if not DOCLING_AVAILABLE:
            logger.warning("Docling not available. Will use fallback extraction methods.")
            self.converter = None
        else:
            try:
                # Initialize DocumentConverter with optimized settings
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = False  # We'll use PaddleOCR as fallback
                pipeline_options.do_table_structure = True
                pipeline_options.table_structure_options.do_cell_matching = True
                
                self.converter = DocumentConverter(
                    format=InputFormat.PDF,
                    pipeline_options=pipeline_options
                )
                logger.info("Docling initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Docling: {e}. Will use fallback.")
                self.docling_available = False
                self.converter = None
    
    def parse_pdf_to_structured_text(self, filepath: str) -> Dict[str, Any]:
        """
        Parse PDF to structured text using Docling (with fallback)
        Returns: {
            full_text: str,
            section_chunks: List[Dict],
            tables_text: str,
            sections: List[Dict]
        }
        """
        # Fallback if Docling not available
        if not self.docling_available or not self.converter:
            return self._fallback_extraction(filepath)
        
        try:
            # Basic corrupted-PDF validation using pypdf
            try:
                import pypdf
                with open(filepath, "rb") as f:
                    pypdf.PdfReader(f)  # Will raise on severely corrupted PDFs
            except Exception as pdf_err:
                logger.error(f"Invalid or corrupted PDF file: {pdf_err}")
                return {
                    "full_text": "",
                    "section_chunks": [],
                    "tables_text": "",
                    "sections": [],
                    "page_count": 0,
                    "has_text": False,
                    "error": "Invalid or corrupted PDF file"
                }

            # Convert document with timeout protection (15 seconds max)
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
            
            def run_docling():
                return self.converter.convert(filepath)
            
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_docling)
                    result = future.result(timeout=15)  # 15 second timeout
            except FuturesTimeoutError:
                logger.warning(f"⏱️ Docling parsing timed out after 15s for {filepath}, using fallback...")
                return self._fallback_extraction(filepath)
            except Exception as docling_err:
                logger.warning(f"Docling conversion failed: {docling_err}, using fallback...")
                return self._fallback_extraction(filepath)
            
            doc = result.document
            
            # Extract full text
            full_text_parts = []
            section_chunks = []
            tables_text_parts = []
            sections = []
            
            # Process document structure
            current_section = None
            current_page = 1
            
            for item in doc.items:
                # Extract text from different item types
                if hasattr(item, 'text'):
                    text = item.text
                    if text and text.strip():
                        full_text_parts.append(text.strip())
                        
                        # Track sections
                        if hasattr(item, 'level') and item.level:
                            # This is a heading
                            section_name = text.strip()
                            current_section = {
                                "title": section_name,
                                "level": item.level,
                                "page": current_page,
                                "content": []
                            }
                            sections.append(current_section)
                        elif current_section:
                            current_section["content"].append(text.strip())
                        else:
                            # No section, create default
                            if not sections:
                                current_section = {
                                    "title": "Introduction",
                                    "level": 1,
                                    "page": current_page,
                                    "content": []
                                }
                                sections.append(current_section)
                            current_section["content"].append(text.strip())
                
                # Extract tables
                if hasattr(item, 'table') and item.table:
                    table_text = self._table_to_text(item.table)
                    tables_text_parts.append(table_text)
                    full_text_parts.append(f"\n[TABLE]\n{table_text}\n[/TABLE]\n")
                
                # Track page numbers
                if hasattr(item, 'page') and item.page:
                    current_page = item.page
            
            # Combine all text
            full_text = "\n\n".join(full_text_parts)
            tables_text = "\n\n".join(tables_text_parts)

            # Debug: log Docling extraction stats
            logger.info(f"DOC LING FULL TEXT LENGTH: {len(full_text)}")
            logger.info(f"DOC LING SECTIONS COUNT: {len(sections)}")
            logger.info(f"DOC LING TABLE TEXT LENGTH: {len(tables_text)}")

            # Debug: write to disk per-file in storage/debug
            try:
                debug_dir = Path("storage") / "debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                stem = Path(filepath).stem

                full_path = debug_dir / f"{stem}_full_text_docling.txt"
                sections_path = debug_dir / f"{stem}_sections_docling.json"
                tables_path = debug_dir / f"{stem}_tables_docling.txt"

                with open(full_path, "w", encoding="utf-8") as f_full:
                    f_full.write(full_text)
                with open(sections_path, "w", encoding="utf-8") as f_sec:
                    json.dump(sections, f_sec, ensure_ascii=False, indent=2)
                with open(tables_path, "w", encoding="utf-8") as f_tab:
                    f_tab.write(tables_text)
            except Exception as debug_err:
                logger.warning(f"Failed to write Docling debug files: {debug_err}")
            
            # Create section chunks
            for section in sections:
                section_text = "\n".join(section["content"])
                section_chunks.append({
                    "title": section["title"],
                    "level": section["level"],
                    "page": section.get("page", 1),
                    "text": section_text
                })
            
            return {
                "full_text": full_text,
                "section_chunks": section_chunks,
                "tables_text": tables_text,
                "sections": sections,
                "page_count": current_page,
                "has_text": len(full_text.strip()) > 0
            }
            
        except Exception as e:
            logger.error(f"Docling parsing error: {e}")
            return {
                "full_text": "",
                "section_chunks": [],
                "tables_text": "",
                "sections": [],
                "page_count": 0,
                "has_text": False,
                "error": str(e)
            }
    
    def extract_tables(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF using Docling
        Returns: List of table dictionaries
        """
        try:
            result = self.converter.convert(filepath)
            doc = result.document
            
            tables = []
            for item in doc.items:
                if hasattr(item, 'table') and item.table:
                    table_data = self._table_to_dict(item.table)
                    tables.append(table_data)
            
            return tables
            
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
            return []
    
    def extract_sections(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Extract document sections with headers
        Returns: List of section dictionaries
        """
        try:
            result = self.parse_pdf_to_structured_text(filepath)
            return result.get("sections", [])
            
        except Exception as e:
            logger.error(f"Section extraction error: {e}")
            return []
    
    def _table_to_text(self, table) -> str:
        """Convert Docling table to text format"""
        try:
            rows = []
            if hasattr(table, 'rows'):
                for row in table.rows:
                    cells = []
                    if hasattr(row, 'cells'):
                        for cell in row.cells:
                            if hasattr(cell, 'text'):
                                cells.append(cell.text or "")
                            else:
                                cells.append(str(cell))
                    rows.append(" | ".join(cells))
            return "\n".join(rows)
        except Exception as e:
            logger.warning(f"Table to text conversion error: {e}")
            return ""
    
    def _table_to_dict(self, table) -> Dict[str, Any]:
        """Convert Docling table to dictionary"""
        try:
            rows = []
            if hasattr(table, 'rows'):
                for row in table.rows:
                    cells = []
                    if hasattr(row, 'cells'):
                        for cell in row.cells:
                            if hasattr(cell, 'text'):
                                cells.append(cell.text or "")
                            else:
                                cells.append(str(cell))
                    rows.append(cells)
            
            return {
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(rows[0]) if rows else 0
            }
        except Exception as e:
            logger.warning(f"Table to dict conversion error: {e}")
            return {"rows": [], "row_count": 0, "column_count": 0}
    
    def _fallback_extraction(self, filepath: str) -> Dict[str, Any]:
        """Fallback extraction using PyPDF when Docling is not available"""
        try:
            import pypdf
            
            full_text_parts = []
            with open(filepath, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        full_text_parts.append(f"[Page {page_num + 1}]\n{text}")
            
            full_text = "\n\n".join(full_text_parts)

            # Debug: log fallback extraction stats
            logger.info(f"FALLBACK FULL TEXT LENGTH: {len(full_text)} (pypdf)")
            
            result = {
                "full_text": full_text,
                "section_chunks": [],
                "tables_text": "",
                "sections": [],
                "page_count": num_pages if full_text_parts else 0,
                "has_text": len(full_text.strip()) > 0
            }

            # Debug: also write fallback text to disk
            try:
                debug_dir = Path("storage") / "debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                stem = Path(filepath).stem
                full_path = debug_dir / f"{stem}_full_text_fallback.txt"
                with open(full_path, "w", encoding="utf-8") as f_full:
                    f_full.write(full_text)
            except Exception as debug_err:
                logger.warning(f"Failed to write fallback debug files: {debug_err}")

            return result
        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return {
                "full_text": "",
                "section_chunks": [],
                "tables_text": "",
                "sections": [],
                "page_count": 0,
                "has_text": False,
                "error": str(e)
            }

