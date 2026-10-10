"""
analysis.py - Pydantic schemas for emotion analysis
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class AnalyzeTextRequest(BaseModel):
    """Request schema for analyzing text"""
    text: str = Field(..., min_length=1, description="Text to analyze")
    return_all_scores: bool = Field(False, description="Return scores for all emotions")


class EmotionScore(BaseModel):
    """Individual emotion score"""
    emotion: str
    confidence: float = Field(... , ge=0.0, le=1.0)


class EmotionAnalysisResponse(BaseModel):
    """Response schema for emotion analysis"""
    emotion: str
    confidence: float
    cleaned_text: str
    all_scores: Optional[Dict[str, float]] = None


class TopEmotionsResponse(BaseModel):
    """Response schema for top K emotions"""
    top_emotions: List[EmotionScore]
    text_preview: str