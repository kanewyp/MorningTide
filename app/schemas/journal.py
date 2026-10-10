"""
journal.py - Pydantic schemas for journal entries
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict


class JournalEntryBase(BaseModel):
    """Base schema for journal entries"""
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1, description="Journal entry text")


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating a new journal entry"""
    pass


class JournalEntryUpdate(BaseModel):
    """Schema for updating an existing journal entry"""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None


class JournalEntryResponse(JournalEntryBase):
    """Schema for journal entry responses"""
    id: int
    user_id: int
    primary_emotion: Optional[str]
    emotion_confidence: Optional[float]
    all_emotion_scores: Optional[Dict[str, float]]
    created_at:  datetime
    updated_at: datetime
    
    class Config: 
        from_attributes = True  # Allows SQLAlchemy models to be converted