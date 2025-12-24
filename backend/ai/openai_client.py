"""
OpenAI client wrapper for GPT-5 Nano/Mini
"""

import openai
from typing import Dict, Any, Optional, List
from config.settings import settings
import json
import logging
from utils.validators import sanitize_json_string, parse_json_safely
from ai.openai_utils import safe_openai_call

logger = logging.getLogger(__name__)

# Initialize OpenAI client
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY
else:
    logger.warning("OPENAI_API_KEY not set. AI features will not work.")

class OpenAIClient:
    def __init__(self):
        # Use exact model names from settings (gpt-5-nano and gpt-5-mini)
        self.primary_model = settings.OPENAI_MODEL_PRIMARY
        self.fallback_model = settings.OPENAI_MODEL_FALLBACK
        
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is required. Please set it in .env file.")
            raise ValueError("OPENAI_API_KEY is required. Please set it in .env file or environment variables.")
        
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"OpenAI Client initialized - Primary: {self.primary_model}, Fallback: {self.fallback_model}")
    
    def classify_blocks(
        self,
        text: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Semantic block classification - identifies which information blocks appear in text
        Returns: {blocks_detected: [...], confidence: 0.0-1.0, snippet: "...", page: 1}
        """
        from config.information_blocks import get_information_blocks, get_block_description
        
        blocks = get_information_blocks()
        block_descriptions = []
        
        for block_id in blocks:
            desc = get_block_description(block_id)
            block_descriptions.append(
                f"- {block_id}: {desc.get('description', '')} "
                f"(Keywords: {', '.join(desc.get('keywords', [])[:5])})"
            )
        
        prompt = f"""You are a semantic information block classifier for {mode.upper()} institutional document review.

Analyze the following text chunk and identify which INFORMATION BLOCKS are present.
A single chunk may contain MULTIPLE blocks.

Available Information Blocks:
{chr(10).join(block_descriptions)}

IMPORTANT: Use SEMANTIC understanding, not just keyword matching:
- "teaching staff" or "educators" → faculty_information
- "career outcomes" or "job placements" → placement_information
- "built-up area" or "campus infrastructure" → infrastructure_information
- "academic schedule" or "semester dates" → academic_calendar_information
- "fire safety certificate" or "fire NOC" → safety_compliance_information

Text chunk (first 3000 characters):
{text[:3000]}

Return a JSON object with:
{{
    "blocks_detected": ["block_type1", "block_type2", ...],
    "confidence": 0.0-1.0,
    "snippet": "relevant text snippet that supports the classification",
    "page": 1
}}

Be precise. Only include blocks that are CLEARLY present. Return empty array if none match."""

        try:
            response = safe_openai_call(
                self.client,
                self.primary_model,
                [
                    {"role": "system", "content": "You are a precise semantic classifier. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = parse_json_safely(result_text)
            
            # Validate result
            if "blocks_detected" not in result:
                result["blocks_detected"] = []
            if "confidence" not in result:
                result["confidence"] = 0.0
            if "snippet" not in result:
                result["snippet"] = ""
            
            return result
            
        except Exception as e:
            logger.error(f"Block classification error: {e}")
            return {
                "blocks_detected": [],
                "confidence": 0.0,
                "snippet": "",
                "page": None
            }
    
    # DEPRECATED: Document-type classification removed
    # System now uses information block classification only
    
    def extract_block_data(
        self,
        block_type: str,
        text: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from a specific information block
        Returns: {extracted_data: {...}, confidence: 0.0-1.0, evidence: [...]}
        """
        from config.information_blocks import get_block_fields, get_block_description
        
        block_desc = get_block_description(block_type)
        block_fields = get_block_fields(block_type, mode)
        
        required_fields = block_fields.get("required_fields", [])
        optional_fields = block_fields.get("optional_fields", [])
        
        # Build extraction schema
        schema_fields = []
        for field in required_fields + optional_fields:
            schema_fields.append(f"- {field}: Extract this field if mentioned")
        
        prompt = f"""You are a semantic data extraction specialist for {mode.upper()} institutional document review.

Extract structured data from this {block_type} block.

Block Description: {block_desc.get('description', '')}
Synonyms to recognize: {', '.join(block_desc.get('synonyms', []))}

Text chunk:
{text[:6000]}

Extract the following fields (use SEMANTIC understanding):
{chr(10).join(schema_fields)}

IMPORTANT: 
- Use semantic understanding: "teaching staff: 60" → faculty_count = 60
- "educators: 60" → faculty_count = 60
- "20 professors + 40 lecturers" → faculty_count = 60
- Extract meaning even with synonyms or indirect phrasing
- If a field is not found, use null
- Extract ALL numeric values mentioned (counts, percentages, areas, etc.)

Return a JSON object with:
{{
    "extracted_data": {{
        "field1": value1,
        "field2": value2,
        ...
    }},
    "confidence": 0.0-1.0,
    "evidence": [
        {{
            "field": "field_name",
            "value": "extracted_value",
            "page": 1,
            "snippet": "supporting text"
        }}
    ]
}}

Be precise. Always return valid JSON."""

        try:
            response = safe_openai_call(
                self.client,
                self.primary_model,
                [
                    {"role": "system", "content": "You are a precise data extractor. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = parse_json_safely(result_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Block extraction error: {e}")
            return {
                "extracted_data": {},
                "confidence": 0.0,
                "evidence": []
            }
    
    # DEPRECATED: Document-type extraction removed
    # System now uses block-based extraction only (extract_block_data)
    
    def chat(
        self,
        message: str,
        context: Dict[str, Any],
        mode: str
    ) -> str:
        """
        Chatbot assistant using GPT-5 Nano
        Uses information blocks context, not documents
        
        Args:
            message: User query/question
            context: Dict containing 'system_prompt' (optional) and other context data
            mode: 'aicte' or 'ugc'
        
        Returns:
            Response text from GPT-5 Nano
        """
        # Extract system prompt from context if provided, otherwise use default
        system_prompt = context.get("system_prompt")
        if not system_prompt:
            # Default system prompt for backward compatibility
            context_str = json.dumps(context, indent=2)
            system_prompt = f"""You are a helpful assistant for {mode.upper()} reviewers analyzing institutional information blocks.

The system extracts 10 information blocks from uploaded documents:
1. Faculty Information
2. Student Enrollment Information
3. Infrastructure Information
4. Lab & Equipment Information
5. Safety & Compliance Information
6. Academic Calendar Information
7. Fee Structure Information
8. Placement Information
9. Research & Innovation Information
10. Mandatory Committees Information

Context from the current batch:
{context_str}

Provide a clear, helpful answer based on the information blocks context. 
- Explain KPIs using block data
- Explain sufficiency formula: base_pct = (P/R)*100, penalty = O*4 + L*5 + I*7
- Explain missing blocks, outdated blocks, invalid blocks
- Summarize institution status based on blocks

If you don't know, say so."""
            user_content = message
        else:
            # Use provided system prompt and message as user content
            user_content = message

        # Map custom model names to real OpenAI models if needed
        model_mapping = {
            "gpt-5-nano": "gpt-4o-mini",  # Use GPT-4o-mini as replacement
            "gpt-5-mini": "gpt-4o-mini",  # Use GPT-4o-mini as replacement
        }
        
        actual_primary = model_mapping.get(self.primary_model, self.primary_model)
        actual_fallback = model_mapping.get(self.fallback_model, self.fallback_model)
        
        try:
            # Explicitly use primary model for chatbot
            logger.info(f"Calling {actual_primary} (configured as {self.primary_model}) for chatbot query")
            response = safe_openai_call(
                self.client,
                actual_primary,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7
            )
            
            if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
                raise ValueError("Empty or invalid response from OpenAI API")
            
            logger.info(f"{actual_primary} response received successfully")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Chat error ({actual_primary}): {e}", exc_info=True)
            # Try fallback model if primary fails
            try:
                logger.info(f"Trying fallback model {actual_fallback} (configured as {self.fallback_model}) for chatbot")
                response = safe_openai_call(
                    self.client,
                    actual_fallback,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7
                )
                
                if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
                    raise ValueError("Empty or invalid response from fallback model")
                
                return response.choices[0].message.content
            except Exception as e2:
                logger.error(f"Chat error with fallback model ({actual_fallback}): {e2}", exc_info=True)
                # Return a more helpful error message
                error_str = str(e2).lower()
                if "model" in error_str and ("not found" in error_str or "invalid" in error_str):
                    return f"I apologize, but there's an issue with the AI model configuration. The model '{self.primary_model}' is not available. Please check your OpenAI API configuration."
                elif "api key" in error_str or "authentication" in error_str:
                    return "I apologize, but there's an authentication issue with the AI service. Please check your OpenAI API key configuration."
                elif "rate limit" in error_str or "quota" in error_str:
                    return "I apologize, but the AI service is currently rate-limited. Please try again in a moment."
                else:
                    return f"I apologize, but I'm having trouble processing your request. Error: {str(e2)[:100]}"

