"""
Pydantic schemas for RAG API endpoints. 

Defines request/response models for validation and documentation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== Request Models ====================

class DiaryEntrySchema(BaseModel):
    """Schema for a diary entry."""
    date: str = Field(
        ...,
        description="Entry date in ISO format (YYYY-MM-DD)",
        example="2026-01-16"
    )
    content: str = Field(
        ...,
        description="Diary entry text content",
        example="Today was challenging.  I felt anxious about the presentation..."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-16",
                "content": "Today I felt overwhelmed with work and had trouble sleeping."
            }
        }


class GenerateSuggestionsRequestSchema(BaseModel):
    """Schema for generating suggestions request."""
    diary_entries: List[DiaryEntrySchema] = Field(
        ...,
        description="List of recent diary entries (up to 7 days recommended)",
        min_items=1,
        max_items=30
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of therapy topics to retrieve and use as context"
    )
    stream: bool = Field(
        False,
        description="Whether to stream the LLM response (experimental)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "diary_entries": [
                    {
                        "date": "2026-01-16",
                        "content": "Feeling anxious about upcoming work presentation..."
                    },
                    {
                        "date": "2026-01-15",
                        "content": "Slept poorly, mind racing with worries..."
                    }
                ],
                "top_k":  5,
                "stream":  False
            }
        }


# ==================== Response Models ====================

class DiaryAnalysisSchema(BaseModel):
    """Analysis of diary entries."""
    entry_count: int = Field(
        .. .,
        description="Number of entries analyzed"
    )
    date_range: str = Field(
        ...,
        description="Date range of entries (e.g., '2026-01-10 to 2026-01-16')"
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Identified themes/keywords from entries"
    )


class TherapyTopicSchema(BaseModel):
    """Schema for a therapy topic from corpus."""
    id: str = Field(... , description="Unique topic identifier")
    category: str = Field(..., description="Topic category (e.g., 'Anxiety Management')")
    title: str = Field(..., description="Topic title")
    content: str = Field(..., description="Detailed topic content")
    keywords: List[str] = Field(default_factory=list, description="Associated keywords")
    difficulty: str = Field(..., description="Difficulty level:  beginner/intermediate/advanced")
    similarity_score: Optional[float] = Field(
        None,
        description="Semantic similarity score to user context (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id":  "anxiety_001",
                "category": "Anxiety Management",
                "title":  "Understanding Anxiety Triggers",
                "content": "Anxiety often stems from identifiable triggers.. .",
                "keywords": ["anxiety", "triggers", "coping"],
                "difficulty": "beginner",
                "similarity_score":  0.87
            }
        }


class GenerateSuggestionsResponseSchema(BaseModel):
    """Response schema for therapy suggestions."""
    status: str = Field(
        .. .,
        description="Status: 'success' or 'error'"
    )
    timestamp: str = Field(
        .. .,
        description="ISO timestamp when suggestions were generated"
    )
    diary_analysis: DiaryAnalysisSchema = Field(
        ...,
        description="Analysis of the provided diary entries"
    )
    retrieved_topics_count: int = Field(
        ...,
        description="Number of therapy topics retrieved"
    )
    retrieved_topics: List[TherapyTopicSchema] = Field(
        default_factory=list,
        description="Top therapy topics used as context"
    )
    suggestions: str = Field(
        ...,
        description="Generated therapy discussion prompts and suggestions"
    )
    model:  str = Field(
        ...,
        description="LLM model used for generation (e.g., 'mistral')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2026-01-16T14:30:00",
                "diary_analysis": {
                    "entry_count":  3,
                    "date_range": "2026-01-14 to 2026-01-16",
                    "themes":  ["anxiety", "sleep", "work"]
                },
                "retrieved_topics_count":  5,
                "retrieved_topics": [],
                "suggestions": "DISCUSSION TOPIC 1: Managing Work Anxiety\n- Context: Your recent entries show.. .",
                "model": "mistral"
            }
        }


class HealthCheckResponseSchema(BaseModel):
    """Health check response."""
    status: str = Field(... , description="Overall system status")
    embedder:  dict = Field(... , description="Embedding model status")
    vector_store: dict = Field(..., description="Vector store status")
    generator: dict = Field(..., description="LLM generator status")
    timestamp: str = Field(..., description="Check timestamp")


class IndexStatsSchema(BaseModel):
    """Vector store index statistics."""
    total_documents: int = Field(... , description="Total documents indexed")
    dimension: int = Field(..., description="Embedding dimension")
    store_path: str = Field(..., description="Path to vector store")
    index_file_exists: bool = Field(..., description="Whether index file exists")
    metadata_file_exists: bool = Field(..., description="Whether metadata file exists")