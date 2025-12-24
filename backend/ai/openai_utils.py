"""
OpenAI API utility functions for safe API calls
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def safe_openai_call(client, model: str, messages: list, timeout: int = 120, **kwargs) -> Optional[Any]:
    """
    Safely call OpenAI API with multiple fallback strategies
    Handles temperature, response_format, and other parameter issues
    Includes timeout protection (default 120s)
    """
    # Strategy 1: Try with response_format (JSON mode) but no temperature
    try:
        if "response_format" in kwargs:
            # Remove temperature if present
            call_kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
            return client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout,
                **call_kwargs
            )
    except Exception as e1:
        logger.debug(f"Strategy 1 failed: {e1}")
        
        # Strategy 2: Try without response_format but with temperature
        try:
            call_kwargs = {k: v for k, v in kwargs.items() if k != "response_format"}
            return client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout,
                **call_kwargs
            )
        except Exception as e2:
            logger.debug(f"Strategy 2 failed: {e2}")
            
            # Strategy 3: Try with minimal parameters
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=timeout
                )
            except Exception as e3:
                logger.error(f"All OpenAI call strategies failed: {e3}")
                raise e3


