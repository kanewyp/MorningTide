"""
Utility Functions for RAG Pipeline

Text processing, chunking, formatting, and other helpers. 
"""

import re
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64
) -> List[str]:
    """
    Split text into overlapping chunks by word count. 

    Args:
        text: Text to chunk
        chunk_size:  Target size of each chunk (in words)
        overlap: Number of words to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def summarize_diary_entries(
    combined_text: str,
    max_length: int = 500
) -> str:
    """
    Create a brief summary of diary entries.

    This is a simplified extractive summary.  For production,
    consider using a dedicated summarization model.

    Args:
        combined_text: Combined diary entry text
        max_length: Maximum summary length in characters

    Returns: 
        Summary text
    """
    if not combined_text or not combined_text.strip():
        return "No diary entries provided."

    # Remove date markers
    cleaned = re.sub(r'\[\d{4}-\d{2}-\d{2}\]', '', combined_text)

    # Extract sentences
    sentences = re.split(r'[.!?]+', cleaned)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return combined_text[: max_length]

    # Build summary by selecting key sentences
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 2 < max_length:
            summary += sentence + ". "
        else:
            break

    return summary. strip() if summary else combined_text[:max_length]


def format_therapy_context(topics: List[dict]) -> str:
    """
    Format therapy topics for LLM context.

    Args:
        topics: List of therapy topic dictionaries

    Returns:
        Formatted context string
    """
    if not topics:
        return ""

    formatted = "## Relevant Therapy Topics for Context:\n\n"

    for i, topic in enumerate(topics, 1):
        formatted += f"**{i}. {topic. get('title', 'Untitled')}**\n"
        formatted += f"- Category: {topic.get('category', 'General')}\n"
        formatted += f"- Level: {topic.get('difficulty', 'N/A')}\n"

        content = topic.get('content', '')
        if len(content) > 200:
            content = content[:200] + "..."

        formatted += f"- Summary: {content}\n\n"

    return formatted


def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
    """
    Extract potential keywords from text (simplified approach).

    For production, use libraries like YAKE or TextRank.

    Args:
        text: Text to extract keywords from
        num_keywords: Number of keywords to extract

    Returns:
        List of keywords
    """
    # Common mental health keywords to look for
    mental_health_keywords = {
        "anxiety":  ["anxiety", "anxious", "worried", "panic", "fear"],
        "depression": ["depression", "depressed", "sad", "hopeless", "worthless"],
        "stress": ["stress", "stressed", "overwhelmed", "pressure", "tension"],
        "sleep": ["sleep", "insomnia", "tired", "exhausted", "fatigue"],
        "relationships": ["relationship", "conflict", "family", "friend", "partner", "lonely"],
        "work": ["work", "job", "career", "boss", "deadline", "performance"],
        "trauma": ["trauma", "triggered", "flashback", "abuse", "violence"],
        "identity": ["identity", "self", "authentic", "belong", "purpose"],
        "motivation": ["motivation", "procrastination", "stuck", "paralyzed", "inertia"],
        "grief": ["grief", "loss", "mourn", "death", "gone"],
    }

    text_lower = text.lower()
    found_keywords = []

    for category, keywords_list in mental_health_keywords. items():
        for keyword in keywords_list:
            if keyword in text_lower and category not in found_keywords:
                found_keywords.append(category)
                break

    return found_keywords[: num_keywords]


def count_tokens(text: str) -> int:
    """
    Estimate token count (rough approximation).

    For accurate counts, use tiktoken library or model-specific tokenizers.

    Args:
        text: Text to count tokens for

    Returns:
        Approximate token count
    """
    # Rough heuristic:  ~4 characters per token on average
    # This varies by model and content
    return len(text) // 4


def truncate_to_token_limit(
    text: str,
    max_tokens: int = 2000,
    tokens_per_char: float = 0.25
) -> str:
    """
    Truncate text to approximate token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        tokens_per_char:  Approximate tokens per character

    Returns: 
        Truncated text
    """
    max_chars = int(max_tokens / tokens_per_char)
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    # Try to cut at a sentence boundary
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:
        truncated = truncated[:last_period + 1]

    return truncated. strip()


def clean_text(text: str) -> str:
    """
    Clean and normalize text. 

    Args:
        text:  Text to clean

    Returns: 
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text. split())

    # Remove HTML tags if present
    text = re.sub(r'<[^>]+>', '', text)

    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)

    return text.strip()