"""
Chatbot assistant router - Full AI chatbot system
Supports comprehensive Q&A about dashboard, KPIs, approval, comparison, trends
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from services.chatbot_service import ChatbotService
from config.database import get_db, Batch, Block, close_db

router = APIRouter()
chatbot_service = ChatbotService()
logger = logging.getLogger(__name__)


def get_comparison_data(batch_ids: List[str], db) -> Optional[Dict[str, Any]]:
    """Helper to get comparison data for chatbot context."""
    try:
        from routers.compare import compare_institutions
        from fastapi import Query
        
        # Call the comparison endpoint logic
        batch_ids_str = ",".join(batch_ids)
        comparison_result = compare_institutions(batch_ids=batch_ids_str)
        
        # Convert Pydantic model to dict
        if hasattr(comparison_result, 'model_dump'):
            return comparison_result.model_dump()
        elif hasattr(comparison_result, 'dict'):
            return comparison_result.dict()
        else:
            return comparison_result
    except Exception as e:
        logger.warning(f"Could not fetch comparison data: {e}")
        # Return basic info if full comparison fails
        return {
            "batch_ids": batch_ids,
            "count": len(batch_ids),
            "note": f"Comparison data unavailable: {str(e)}"
        }


def get_unified_report_data(batch_id: str, db) -> Optional[Dict[str, Any]]:
    """Helper to get unified report data for chatbot context."""
    try:
        from routers.unified_report import get_unified_report
        result = get_unified_report(batch_id)
        if result and hasattr(result, 'model_dump'):
            return result.model_dump()
        elif result and hasattr(result, 'dict'):
            return result.dict()
        elif isinstance(result, dict):
            return result
        return None
    except Exception as e:
        logger.warning(f"Could not fetch unified report data: {e}")
        return None


class ChatQueryRequest(BaseModel):
    query: str
    batch_id: str
    current_page: Optional[str] = "dashboard"
    comparison_batch_ids: Optional[list] = None


class ChatQueryResponse(BaseModel):
    answer: str
    citations: list
    related_blocks: list
    requires_context: bool


@router.get("/health")
def chatbot_health():
    """Check if chatbot service is properly configured."""
    try:
        from config.settings import settings
        
        has_api_key = bool(settings.OPENAI_API_KEY)
        primary_model = settings.OPENAI_MODEL_PRIMARY
        fallback_model = settings.OPENAI_MODEL_FALLBACK
        
        # Try to initialize client
        client_ok = False
        error_msg = None
        try:
            from ai.openai_client import OpenAIClient
            client = OpenAIClient()
            client_ok = True
        except Exception as e:
            client_ok = False
            error_msg = str(e)
        
        return {
            "status": "ok" if (has_api_key and client_ok) else "error",
            "has_api_key": has_api_key,
            "primary_model": primary_model,
            "fallback_model": fallback_model,
            "client_initialized": client_ok,
            "error": error_msg if not client_ok else None
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/query", response_model=ChatQueryResponse)
def query_chatbot(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    Query the chatbot with context from current page.
    
    Supports:
    - Dashboard: KPIs, sufficiency, compliance, blocks
    - Approval: Classification, readiness, required documents
    - Unified Report: Merged AICTE+UGC data
    - Comparison: Multi-institution comparison
    - Trends: Historical trends and forecasts
    """
    db = None
    try:
        # Validate request
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if not request.batch_id:
            raise HTTPException(status_code=400, detail="batch_id is required")
        
        db = get_db()
        
        # Get batch
        batch = db.query(Batch).filter(Batch.id == request.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch {request.batch_id} not found")
        
        # Get all blocks (limit to prevent huge context)
        blocks = db.query(Block).filter(Block.batch_id == request.batch_id).limit(50).all()
        
        # Get page-specific context
        comparison_data = None
        unified_report_data = None
        
        if request.current_page == "compare" and request.comparison_batch_ids:
            # Fetch comparison data
            try:
                comparison_data = get_comparison_data(request.comparison_batch_ids, db)
            except Exception as e:
                logger.warning(f"Could not fetch comparison data: {e}")
        
        elif request.current_page == "unified-report":
            # Fetch unified report data
            try:
                unified_report_data = get_unified_report_data(request.batch_id, db)
            except Exception as e:
                logger.warning(f"Could not fetch unified report data: {e}")
        
        # Build context
        try:
            context = chatbot_service.build_context(
                batch=batch,
                blocks=blocks,
                current_page=request.current_page or "dashboard",
                comparison_data=comparison_data,
                unified_report_data=unified_report_data
            )
        except Exception as e:
            logger.error(f"Error building context: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error building context: {str(e)}")
        
        # Generate response
        try:
            result = chatbot_service.generate_response(
                query=request.query,
                context=context,
                mode=batch.mode or "aicte"
            )
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}", exc_info=True)
            # Return a fallback response instead of crashing
            result = {
                "answer": f"I apologize, but I encountered an error processing your question: {str(e)[:200]}. Please try again or contact support.",
                "citations": [],
                "related_blocks": [],
                "requires_context": False
            }
        
        return ChatQueryResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query_chatbot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)[:200]}")
    finally:
        if db:
            close_db(db)


# Keep old endpoint for backward compatibility
@router.post("/chat")
def chat_with_assistant(message: Dict[str, Any]):
    """Legacy endpoint - redirects to new query endpoint"""
    return query_chatbot(ChatQueryRequest(
        query=message.get("message", ""),
        batch_id=message.get("batch_id", ""),
        current_page=message.get("current_page", "dashboard")
    ))
