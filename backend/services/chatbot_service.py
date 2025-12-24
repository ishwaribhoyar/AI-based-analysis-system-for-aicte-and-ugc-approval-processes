"""
Chatbot Service for Smart Approval AI.
Provides intelligent responses based on real extracted data.
"""

import logging
from typing import Dict, Any, List, Optional
from ai.openai_client import OpenAIClient
import json

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self):
        self.ai_client = OpenAIClient()
    
    def build_context(
        self,
        batch: Any,
        blocks: List[Any],
        current_page: str = "dashboard",
        comparison_data: Optional[Dict] = None,
        unified_report_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context from batch data.
        """
        # Aggregate block data
        block_data = {}
        block_summaries = {}
        
        for block in blocks:
            block_type = block.block_type
            data = block.data or {}
            
            # Aggregate data (merge multiple blocks of same type)
            if block_type not in block_data:
                block_data[block_type] = {}
            
            # Merge data, preferring _num fields for numeric values
            for key, value in data.items():
                if key.endswith("_num") and isinstance(value, (int, float)):
                    # For numeric fields, take the maximum value
                    if key in block_data[block_type]:
                        block_data[block_type][key] = max(block_data[block_type][key], value)
                    else:
                        block_data[block_type][key] = value
                else:
                    # For non-numeric fields, update if not already present
                    if key not in block_data[block_type] or block_data[block_type][key] in [None, "", []]:
                        block_data[block_type][key] = value
            
            # Build summary (keep most recent/confident block info)
            if block_type not in block_summaries or block.confidence > block_summaries[block_type].get("confidence", 0):
                block_summaries[block_type] = {
                    "present": True,
                    "confidence": block.confidence,
                    "fields_count": len([k for k, v in data.items() if v not in [None, "", []]]),
                    "is_outdated": bool(block.is_outdated),
                    "is_low_quality": bool(block.is_low_quality),
                    "is_invalid": bool(block.is_invalid),
                    "evidence_snippet": block.evidence_snippet[:300] if block.evidence_snippet else None,
                    "evidence_page": block.evidence_page,
                    "source_doc": block.source_doc,
                    "sample_fields": {k: v for k, v in list(data.items())[:5] if v not in [None, "", []]}  # Sample of extracted fields
                }
        
        # Build context
        context = {
            "batch_id": batch.id,
            "mode": batch.mode,
            "current_page": current_page,
            "kpi_results": batch.kpi_results or {},
            "sufficiency_result": batch.sufficiency_result or {},
            "compliance_results": batch.compliance_results or [],
            "approval_classification": batch.approval_classification or {},
            "approval_readiness": batch.approval_readiness or {},
            "trend_results": batch.trend_results or {},
            "block_data": block_data,
            "block_summaries": block_summaries,
            "comparison_data": comparison_data,
            "unified_report_data": unified_report_data
        }
        
        return context
    
    def get_kpi_formulas(self, mode: str) -> Dict[str, str]:
        """
        Get KPI calculation formulas for explanation.
        """
        formulas = {}
        
        if mode.lower() == "aicte":
            formulas = {
                "fsr_score": """
                FSR (Faculty-Student Ratio) Score:
                - FSR = Total Faculty / Total Students
                - If FSR >= 0.05 (1:20) → Score = 100
                - If 0.04 (1:25) <= FSR < 0.05 (1:20) → Score = 60
                - If FSR < 0.04 (1:25) → Score = 0
                - If faculty or students missing → Score = None
                """,
                "infrastructure_score": """
                Infrastructure Score (Weighted):
                - Area (40%): score_area = min(100, (actual_area_sqm / required_area) * 100)
                  where required_area = total_students * 4 sqm
                - Classrooms (25%): score_classrooms = min(100, (actual_classrooms / required_classrooms) * 100)
                  where required_classrooms = ceil(total_students / 40)
                - Library (15%): score_library = min(100, (library_area_sqm / (total_students * 0.5)) * 100)
                - Digital (10%): score_digital = min(100, (digital_resources / 500) * 100)
                - Hostel (10%): score_hostel = min(100, (hostel_capacity / (total_students * 0.4)) * 100)
                - Final Score = 0.40 * area + 0.25 * classrooms + 0.15 * library + 0.10 * digital + 0.10 * hostel
                """,
                "placement_index": """
                Placement Index:
                - Placement Rate = (Students Placed / Students Eligible) * 100
                - Final Score = min(placement_rate, 100)
                - If placement_rate is directly available, use it
                - Otherwise calculate from: (students_placed / students_eligible) * 100
                - If required data missing → Score = None
                """,
                "lab_compliance_index": """
                Lab Compliance Index:
                - Required Labs = max(5, total_students // 50)  [At least 1 lab per 50 students, minimum 5]
                - Lab Compliance = (actual_labs / required_labs) * 100, capped at 100
                - Final Score = min(lab_compliance, 100)
                - If actual_labs or student_count missing → Score = None
                """,
                "overall_score": """
                AICTE Overall Score:
                - If FSR available: Average of (FSR + Placement + Lab)
                - If FSR missing: Average of (Infrastructure + Placement + Lab)
                - Infrastructure is excluded when FSR is present to avoid double-weighting
                """
            }
        else:  # UGC
            formulas = {
                "research_index": """
                Research Index:
                - Publications Score = min(100, (publications / 10) * 100)
                - Patents Score = min(100, (patents / 5) * 100)
                - Projects Score = min(100, (funded_projects / 3) * 100)
                - Final Score = 0.4 * publications + 0.3 * patents + 0.3 * projects
                """,
                "governance_score": """
                Governance Score:
                - Committee Presence: 1 point per active committee (IQAC, Anti-Ragging, ICC, Grievance)
                - Score = (active_committees / 4) * 100
                """,
                "student_outcome_index": """
                Student Outcome Index:
                - Placement Rate = (placed / eligible) * 100
                - Academic Performance = average exam scores (if available)
                - Final Score = 0.6 * placement_rate + 0.4 * academic_performance
                """,
                "overall_score": """
                UGC Overall Score:
                - Overall = 0.3 * Research + 0.3 * Governance + 0.4 * Student Outcome
                """
            }
        
        return formulas
    
    def build_system_prompt(self, mode: str, formulas: Dict[str, str]) -> str:
        """
        Build system prompt for the chatbot.
        """
        return f"""You are the Smart Approval AI Chat Assistant for the {mode.upper()} evaluation dashboard.

CRITICAL RULES:
1. You MUST ONLY answer questions related to:
   - This evaluation platform and dashboard
   - AICTE/UGC guidelines and norms
   - KPI scoring (FSR, Infrastructure, Placement, Lab Index, etc.)
   - Document blocks extracted from uploaded files
   - Approval classification (new/renewal, AICTE/UGC/Mixed)
   - Required documents and approval readiness
   - Unified AICTE+UGC reports
   - Institution comparison results
   - Trends and forecasts

2. STRICT SCOPE ENFORCEMENT:
   - If the user asks about general topics (weather, news, other websites, unrelated topics), 
     immediately reply: "I can only answer questions related to your institution evaluation dashboard."
   - Do NOT answer questions about: general knowledge, other institutions (unless in comparison context),
     unrelated educational topics, or anything outside this platform.
   - ONLY answer questions about: this dashboard, uploaded documents, KPIs, approval status, 
     comparison results, trends from this data, and AICTE/UGC norms.

3. DATA ACCURACY - CRITICAL:
   - You MUST use ONLY the provided context data. NEVER hallucinate or make up numbers.
   - If a KPI value is None or missing, say "This KPI could not be calculated" - do NOT guess.
   - If a document is missing, reference the exact missing_documents list from approval_readiness.
   - If data is not in context, say: "This information is not available in your uploaded documents."

4. If information is missing from the context, reply with:
   "This information is not available in your uploaded documents."

5. When explaining KPIs, use the exact formulas provided:
{json.dumps(formulas, indent=2)}

6. When explaining missing documents, reference the approval_readiness data.

7. When explaining comparison results, reference the comparison_data.

8. Format your responses in clear, professional markdown.
   - Use bullet points for lists
   - Use **bold** for important metrics
   - Use code blocks for formulas
   - Use tables when appropriate

9. Always cite which data source you're using (e.g., "Based on your KPI results..." or "According to your extracted blocks...").

10. Be concise but thorough. Provide actionable insights when possible."""
    
    def generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """
        Generate chatbot response with citations.
        """
        # Get formulas
        formulas = self.get_kpi_formulas(mode)
        
        # Build system prompt
        system_prompt = self.build_system_prompt(mode, formulas)
        
        # Build user prompt with context
        context_json = json.dumps(context, indent=2, default=str)
        
        user_prompt = f"""User Question: {query}

Available Context Data:
{context_json}

Please answer the user's question using ONLY the context data provided above. 
If the question is outside the platform scope, politely redirect.
If data is missing, state that clearly.
If explaining KPIs, use the formulas provided in the system prompt."""

        # Generate response using GPT-5 Nano
        try:
            # Truncate context if too large (OpenAI has token limits)
            # Keep essential data but limit block_data size
            context_size = len(context_json)
            if context_size > 50000:  # Roughly 12k tokens, leave room for prompt
                logger.warning(f"Context is large ({context_size} chars), truncating block_data")
                # Keep summaries but truncate detailed block_data
                for block_type in list(context.get("block_data", {}).keys()):
                    block_data = context["block_data"][block_type]
                    # Keep only _num fields and essential fields
                    truncated = {k: v for k, v in block_data.items() if k.endswith("_num") or k in ["faculty_count", "total_students", "built_up_area", "placement_rate"]}
                    context["block_data"][block_type] = truncated
                context_json = json.dumps(context, indent=2, default=str)
            
            # Use gpt-4o-mini specifically for chatbot (not the global model)
            # This keeps extraction using gpt-5-nano while chatbot uses a real OpenAI model
            logger.info(f"Generating chatbot response using gpt-4o-mini for mode: {mode}, query length: {len(query)}")
            logger.debug(f"Context size: {len(context_json)} characters")
            
            # Make direct OpenAI API call with gpt-4o-mini
            CHATBOT_MODEL = "gpt-4o-mini"
            try:
                response = self.ai_client.client.chat.completions.create(
                    model=CHATBOT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    timeout=60
                )
                response_text = response.choices[0].message.content
            except Exception as direct_err:
                logger.warning(f"gpt-4o-mini failed: {direct_err}, trying fallback")
                # Fallback to gpt-3.5-turbo if gpt-4o-mini fails
                response = self.ai_client.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    timeout=60
                )
                response_text = response.choices[0].message.content
            
            if not response_text or len(response_text.strip()) == 0:
                raise ValueError("Empty response from AI client")
            
            logger.info("Chatbot response generated successfully using gpt-4o-mini")
            
            # Extract citations and related blocks
            citations = self._extract_citations(response_text, context)
            related_blocks = self._extract_related_blocks(query, context)
            
            return {
                "answer": response_text,
                "citations": citations,
                "related_blocks": related_blocks,
                "requires_context": False
            }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error generating chatbot response: {e}")
            logger.error(f"Error details: {error_details}")
            
            # Provide a more helpful error message
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                return {
                    "answer": "I apologize, but there's an authentication issue with the AI service. Please contact support.",
                    "citations": [],
                    "related_blocks": [],
                    "requires_context": False
                }
            elif "rate limit" in error_msg or "quota" in error_msg:
                return {
                    "answer": "I apologize, but the AI service is currently rate-limited. Please try again in a moment.",
                    "citations": [],
                    "related_blocks": [],
                    "requires_context": False
                }
            elif "model" in error_msg or "not found" in error_msg:
                return {
                    "answer": "I apologize, but there's an issue with the AI model configuration. Please contact support.",
                    "citations": [],
                    "related_blocks": [],
                    "requires_context": False
                }
            else:
                # For other errors, try to provide a basic response based on context
                return self._generate_fallback_response(query, context, mode)
    
    def _extract_citations(self, response: str, context: Dict[str, Any]) -> List[str]:
        """
        Extract citation sources from response.
        """
        citations = []
        
        # Check which data sources were likely used
        if "kpi" in response.lower() or "score" in response.lower():
            citations.append("KPI Results")
        
        if "sufficiency" in response.lower() or "sufficient" in response.lower():
            citations.append("Sufficiency Analysis")
        
        if "compliance" in response.lower() or "flag" in response.lower():
            citations.append("Compliance Results")
        
        if "approval" in response.lower() or "readiness" in response.lower():
            citations.append("Approval Readiness")
        
        if "trend" in response.lower() or "forecast" in response.lower():
            citations.append("Trend Analysis")
        
        if "comparison" in response.lower() or "compare" in response.lower():
            citations.append("Institution Comparison")
        
        if "block" in response.lower() or "document" in response.lower():
            citations.append("Extracted Blocks")
        
        return citations if citations else ["Dashboard Data"]
    
    def _extract_related_blocks(self, query: str, context: Dict[str, Any]) -> List[str]:
        """
        Extract related block types from query.
        """
        query_lower = query.lower()
        related = []
        
        block_keywords = {
            "faculty": "faculty_information",
            "student": "student_enrollment_information",
            "infrastructure": "infrastructure_information",
            "lab": "lab_information",
            "placement": "placement_information",
            "fee": "fee_structure_information",
            "calendar": "academic_calendar_information",
            "safety": "safety_compliance_information",
            "research": "research_publications_information",
            "committee": "governance_committees_information",
            "governance": "governance_committees_information"
        }
        
        for keyword, block_type in block_keywords.items():
            if keyword in query_lower:
                block_summaries = context.get("block_summaries", {})
                if block_type in block_summaries:
                    related.append(block_type)
        
        return related
    
    def _generate_fallback_response(
        self,
        query: str,
        context: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """
        Generate a fallback response when AI fails, using simple pattern matching.
        """
        query_lower = query.lower()
        
        # KPI-related queries
        if "kpi" in query_lower or "score" in query_lower:
            kpi_results = context.get("kpi_results", {})
            if kpi_results:
                response = "Here are your KPI scores:\n\n"
                for kpi_id, kpi_data in kpi_results.items():
                    if isinstance(kpi_data, dict):
                        name = kpi_data.get("name", kpi_id)
                        value = kpi_data.get("value")
                        if value is not None:
                            response += f"- **{name}**: {value:.2f}\n"
                        else:
                            response += f"- **{name}**: Not available\n"
                response += "\nFor detailed explanations, please ensure the AI service is properly configured."
                return {
                    "answer": response,
                    "citations": ["KPI Results"],
                    "related_blocks": [],
                    "requires_context": False
                }
        
        # Approval-related queries
        if "approval" in query_lower or "readiness" in query_lower:
            readiness = context.get("approval_readiness", {})
            if readiness:
                score = readiness.get("approval_readiness_score", "N/A")
                response = f"Your approval readiness score is **{score}%**.\n\n"
                missing = readiness.get("approval_missing_documents", [])
                if missing:
                    response += f"Missing documents: {', '.join(missing[:5])}\n"
                return {
                    "answer": response,
                    "citations": ["Approval Readiness"],
                    "related_blocks": [],
                    "requires_context": False
                }
        
        # Default fallback
        return {
            "answer": "I apologize, but I encountered an error processing your question. Please try again, or contact support if the issue persists.",
            "citations": [],
            "related_blocks": [],
            "requires_context": False
        }

