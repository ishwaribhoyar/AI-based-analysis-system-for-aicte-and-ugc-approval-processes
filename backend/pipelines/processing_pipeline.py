"""
DEPRECATED: Main processing pipeline orchestrator
This pipeline uses document-type classification and is no longer used.
The system now uses BlockProcessingPipeline which uses information block architecture.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from config.database import get_database
from models.batch import BatchStatus
from services.routing import RoutingService
from services.preprocessing import PreprocessingService
from ai.openai_client import OpenAIClient
from services.quality import QualityService
from services.sufficiency import SufficiencyService
from services.kpi import KPIService
from services.compliance import ComplianceService
from services.trends import TrendService
from config.rules import get_document_types

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    def __init__(self):
        self.routing = RoutingService()
        self.preprocessing = PreprocessingService()
        self.ai_client = OpenAIClient()
        self.quality = QualityService()
        self.sufficiency = SufficiencyService()
        self.kpi = KPIService()
        self.compliance = ComplianceService()
        self.trends = TrendService()
    
    async def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Main pipeline orchestrator
        Processes batch through all stages
        """
        logger.info(f"🚀 Starting pipeline for batch {batch_id}")
        db = get_database()
        
        try:
            # Update status: ROUTING
            await self._update_batch_status(batch_id, BatchStatus.ROUTING)
            logger.info(f"📋 Stage: ROUTING")
            
            # Get batch and documents
            batch = await db.batches.find_one({"batch_id": batch_id})
            if not batch:
                raise ValueError(f"Batch {batch_id} not found")
            
            mode = batch["mode"]
            documents = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            logger.info(f"📄 Found {len(documents)} documents to process")
            
            if len(documents) == 0:
                logger.warning(f"⚠️  No documents found for batch {batch_id}")
                await self._update_batch_status(batch_id, BatchStatus.COMPLETED)
                return {
                    "status": "completed",
                    "batch_id": batch_id,
                    "message": "No documents to process"
                }
            
            # Stage 1: Routing
            logger.info(f"🔄 Stage 1: Routing documents...")
            for doc in documents:
                if not doc.get("processing_plan"):
                    try:
                        plan = self.routing.create_processing_plan(
                            doc["file_path"],
                            doc["filename"],
                            doc["mime_type"]
                        )
                        await db.documents.update_one(
                            {"document_id": doc["document_id"]},
                            {"$set": {"processing_plan": plan, "status": "routed"}}
                        )
                        logger.info(f"✅ Routed: {doc['filename']}")
                    except Exception as e:
                        logger.error(f"❌ Routing error for {doc['filename']}: {e}")
            
            # Stage 2: Preprocessing
            await self._update_batch_status(batch_id, BatchStatus.PREPROCESSING)
            logger.info(f"🔄 Stage 2: Preprocessing documents...")
            # Refresh documents list to get latest status
            documents = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            for doc in documents:
                if not doc.get("elements"):
                    try:
                        preprocessed = await self.preprocessing.preprocess_document(
                            doc["file_path"],
                            doc["mime_type"]
                        )
                        await db.documents.update_one(
                            {"document_id": doc["document_id"]},
                            {"$set": {
                                "elements": preprocessed["elements"],
                                "extracted_text": preprocessed.get("text", ""),  # Store text separately for easy access
                                "page_images": preprocessed.get("page_images", []),
                                "status": "preprocessed"
                            }}
                        )
                        logger.info(f"✅ Preprocessed: {doc['filename']} ({len(preprocessed.get('elements', []))} elements)")
                    except Exception as e:
                        logger.error(f"❌ Preprocessing error for {doc['filename']}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
            
            # Stage 3: Classification
            await self._update_batch_status(batch_id, BatchStatus.CLASSIFYING)
            logger.info(f"🔄 Stage 3: Classifying documents...")
            available_types = get_document_types(mode)
            # Refresh documents list
            documents = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            
            for doc in documents:
                if not doc.get("doc_type"):
                    try:
                        # Try to get text from stored extracted_text first, then from elements
                        text = doc.get("extracted_text", "") or self._extract_text_from_elements(doc.get("elements", []))
                        text_length = len(text.strip()) if text else 0
                        logger.info(f"📄 Classifying {doc['filename']}: text length = {text_length}")
                        
                        if text and text_length > 50:  # Ensure we have meaningful text
                            # Try filename-based inference first as a hint
                            inferred_type = self._infer_doc_type_from_filename(doc.get("filename", ""), mode)
                            if inferred_type != "unknown":
                                logger.info(f"💡 Filename suggests type: {inferred_type}")
                            
                            classification = await self.ai_client.classify_document(
                                text,
                                mode,
                                available_types
                            )
                            classified_type = classification.get("doc_type", "unknown")
                            confidence = classification.get("confidence", 0)
                            
                            await db.documents.update_one(
                                {"document_id": doc["document_id"]},
                                {"$set": {
                                    "doc_type": classified_type,
                                    "classification_confidence": confidence,
                                    "classification_evidence": classification.get("evidence", {}),
                                    "status": "classified"
                                }}
                            )
                            logger.info(f"✅ Classified: {doc['filename']} as '{classified_type}' (confidence: {confidence:.2f})")
                        else:
                            # Try filename-based inference if text extraction failed
                            inferred_type = self._infer_doc_type_from_filename(doc.get("filename", ""), mode)
                            if inferred_type != "unknown":
                                logger.info(f"💡 Using filename inference: {doc['filename']} -> {inferred_type}")
                                await db.documents.update_one(
                                    {"document_id": doc["document_id"]},
                                    {"$set": {
                                        "doc_type": inferred_type,
                                        "classification_confidence": 0.5,  # Lower confidence for filename-based
                                        "status": "classified"
                                    }}
                                )
                            else:
                                # Mark as failed if no text available and no filename match
                                await db.documents.update_one(
                                    {"document_id": doc["document_id"]},
                                    {"$set": {
                                        "doc_type": "unknown",
                                        "classification_confidence": 0,
                                        "status": "classification_failed",
                                        "processing_errors": [f"No text extracted from document (text length: {text_length})"]
                                    }}
                                )
                                logger.warning(f"⚠️  No text for classification: {doc['filename']} (text length: {text_length})")
                    except Exception as e:
                        logger.error(f"❌ Classification error for {doc['filename']}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Try filename-based inference as fallback
                        inferred_type = self._infer_doc_type_from_filename(doc.get("filename", ""), mode)
                        if inferred_type != "unknown":
                            logger.info(f"💡 Fallback: Using filename inference: {doc['filename']} -> {inferred_type}")
                            await db.documents.update_one(
                                {"document_id": doc["document_id"]},
                                {"$set": {
                                    "doc_type": inferred_type,
                                    "classification_confidence": 0.5,
                                    "status": "classified"
                                }}
                            )
                        else:
                            # Mark document as failed
                            await db.documents.update_one(
                                {"document_id": doc["document_id"]},
                                {"$set": {
                                    "doc_type": "unknown",
                                    "status": "classification_failed",
                                    "processing_errors": [str(e)]
                                }}
                            )
            
            # Stage 4: Extraction
            await self._update_batch_status(batch_id, BatchStatus.EXTRACTING)
            logger.info(f"🔄 Stage 4: Extracting data from documents...")
            # Refresh documents list
            documents = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            for doc in documents:
                if not doc.get("extracted_data"):
                    # Try to infer doc_type from filename if classification failed
                    doc_type = doc.get("doc_type")
                    if not doc_type or doc_type == "unknown":
                        doc_type = self._infer_doc_type_from_filename(doc.get("filename", ""), mode)
                        if doc_type and doc_type != "unknown":
                            logger.info(f"🔍 Inferred doc_type '{doc_type}' from filename: {doc.get('filename')}")
                            await db.documents.update_one(
                                {"document_id": doc["document_id"]},
                                {"$set": {"doc_type": doc_type}}
                            )
                    
                    # Proceed with extraction if we have a doc_type (even if inferred)
                    if doc_type and doc_type != "unknown":
                        try:
                            # Try to get text from stored extracted_text first, then from elements
                            text = doc.get("extracted_text", "") or self._extract_text_from_elements(doc.get("elements", []))
                            if text and len(text.strip()) > 50:  # Ensure we have meaningful text
                                extraction = await self.ai_client.extract_structured_data(
                                    doc_type,
                                    text,
                                    mode
                                )
                                extracted_data = extraction.get("extracted_data", {})
                                await db.documents.update_one(
                                    {"document_id": doc["document_id"]},
                                    {"$set": {
                                        "extracted_data": extracted_data if extracted_data else {},
                                        "extraction_confidence": extraction.get("confidence", 0),
                                        "extraction_evidence": extraction.get("evidence", []),
                                        "status": "extracted"
                                    }}
                                )
                                logger.info(f"✅ Extracted: {doc['filename']} ({len(extracted_data)} fields)")
                            else:
                                # Mark as failed if no text available
                                await db.documents.update_one(
                                    {"document_id": doc["document_id"]},
                                    {"$set": {
                                        "extracted_data": {},
                                        "extraction_confidence": 0,
                                        "status": "extraction_failed",
                                        "processing_errors": [f"No text available for extraction (text length: {len(text) if text else 0})"]
                                    }}
                                )
                                logger.warning(f"⚠️  No text for extraction: {doc['filename']}")
                        except Exception as e:
                            logger.error(f"❌ Extraction error for {doc['filename']}: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            # Mark document as failed but continue
                            await db.documents.update_one(
                                {"document_id": doc["document_id"]},
                                {"$set": {
                                    "extracted_data": {},
                                    "status": "extraction_failed",
                                    "processing_errors": [str(e)]
                                }}
                            )
                    else:
                        logger.warning(f"⚠️  Skipping extraction for {doc.get('filename')}: doc_type is unknown and cannot be inferred")
            
            # Stage 5: Quality Check
            await self._update_batch_status(batch_id, BatchStatus.QUALITY_CHECK)
            logger.info(f"🔄 Stage 5: Quality checking documents...")
            updated_docs = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            doc_list = [dict(doc) for doc in updated_docs]
            
            for doc in doc_list:
                try:
                    quality_result = self.quality.evaluate_document_quality(doc, doc_list)
                    await db.documents.update_one(
                        {"document_id": doc["document_id"]},
                        {"$set": {
                            "quality_flags": quality_result.get("quality_flags", []),
                            "quality_score": quality_result.get("quality_score", 0)
                        }}
                    )
                except Exception as e:
                    logger.error(f"❌ Quality check error for {doc.get('filename', 'unknown')}: {e}")
                    # Continue with default quality values
                    await db.documents.update_one(
                        {"document_id": doc["document_id"]},
                        {"$set": {
                            "quality_flags": [],
                            "quality_score": 0
                        }}
                    )
            
            # Stage 6: Sufficiency
            await self._update_batch_status(batch_id, BatchStatus.SUFFICIENCY)
            logger.info(f"🔄 Stage 6: Calculating sufficiency...")
            # Refresh documents to get latest doc_types
            updated_docs = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            doc_list = [dict(doc) for doc in updated_docs]
            sufficiency_result = self.sufficiency.calculate_sufficiency(mode, doc_list)
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$set": {"sufficiency_result": sufficiency_result}}
            )
            logger.info(f"✅ Sufficiency: {sufficiency_result.get('percentage', 0)}% (Present: {sufficiency_result.get('present_count', 0)}/{sufficiency_result.get('required_count', 0)})")
            
            # Stage 7: KPI Scoring
            await self._update_batch_status(batch_id, BatchStatus.KPI_SCORING)
            logger.info(f"🔄 Stage 7: Calculating KPIs...")
            # Refresh documents to get latest extracted_data
            updated_docs = await db.documents.find({"batch_id": batch_id}).to_list(length=1000)
            doc_list = [dict(doc) for doc in updated_docs]
            kpi_results = self.kpi.calculate_kpis(mode, doc_list)
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$set": {"kpi_results": kpi_results}}
            )
            logger.info(f"✅ KPIs calculated: {len(kpi_results)} metrics")
            # Log KPI values for debugging
            for kpi_id, kpi_data in kpi_results.items():
                if isinstance(kpi_data, dict) and "value" in kpi_data:
                    logger.info(f"   - {kpi_data.get('name', kpi_id)}: {kpi_data.get('value', 0)}")
            
            # Stage 8: Trend Analysis
            await self._update_batch_status(batch_id, BatchStatus.TREND_ANALYSIS)
            logger.info(f"🔄 Stage 8: Analyzing trends...")
            trend_results = await self.trends.analyze_trends(batch_id, mode, kpi_results)
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$set": {"trend_results": trend_results}}
            )
            logger.info(f"✅ Trends analyzed")
            
            # Stage 9: Compliance
            await self._update_batch_status(batch_id, BatchStatus.COMPLIANCE)
            logger.info(f"🔄 Stage 9: Checking compliance...")
            compliance_results = self.compliance.check_compliance(mode, doc_list)
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$set": {"compliance_results": compliance_results}}
            )
            logger.info(f"✅ Compliance checked: {len(compliance_results)} flags")
            
            # Stage 10: Evidence (already collected during extraction)
            await self._update_batch_status(batch_id, BatchStatus.EVIDENCE)
            logger.info(f"🔄 Stage 10: Evidence collection (already done)")
            
            # Stage 11: Report Generation
            await self._update_batch_status(batch_id, BatchStatus.REPORT_GENERATION)
            logger.info(f"🔄 Stage 11: Report generation (on-demand)")
            # Report generation will be handled by report service on demand
            
            # Complete
            await self._update_batch_status(batch_id, BatchStatus.COMPLETED)
            logger.info(f"✅ Pipeline completed successfully for batch {batch_id}")
            
            return {
                "status": "completed",
                "batch_id": batch_id,
                "sufficiency": sufficiency_result,
                "kpis": kpi_results,
                "compliance": compliance_results
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline error for batch {batch_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self._update_batch_status(batch_id, BatchStatus.FAILED)
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$push": {"processing_errors": str(e)}}
            )
            raise
    
    def _extract_text_from_elements(self, elements: list) -> str:
        """Extract text from Unstructured elements"""
        if not elements:
            return ""
        
        text_parts = []
        for elem in elements:
            text = ""
            if isinstance(elem, dict):
                # Handle JSON structure from elements_to_json
                # Try multiple possible keys
                text = (elem.get("text") or 
                       elem.get("content") or 
                       elem.get("text_content") or
                       elem.get("element", {}).get("text", "") if isinstance(elem.get("element"), dict) else "")
                
                # If still no text, try converting the whole dict to string
                if not text:
                    # Look for any string values in the dict
                    for key, value in elem.items():
                        if isinstance(value, str) and len(value) > 10:
                            text = value
                            break
            else:
                # For non-dict elements, convert to string
                text = str(elem)
            
            if text and text.strip():
                text_parts.append(text.strip())
        
        result = "\n\n".join(text_parts)
        return result
    
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
    
    async def _update_batch_status(self, batch_id: str, status: BatchStatus):
        """Update batch status"""
        db = get_database()
        await db.batches.update_one(
            {"batch_id": batch_id},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )

