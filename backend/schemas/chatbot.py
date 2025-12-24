"""
Pydantic schemas for chatbot operations
"""

from pydantic import BaseModel, Field
from typing import List

class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    batch_id: str = Field(..., description="Related batch ID for context")

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

