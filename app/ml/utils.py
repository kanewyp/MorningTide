import re
from typing import List


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex.  
    
    Handles common cases:  
    - Period, exclamation, question marks
    - Preserves abbreviations (Dr., Mr., etc.)
    - Handles ellipsis (...)
    
    Args:
        text: Input text
        
    Returns:  
        List of sentences
    """
    if not text or not text.strip():
        return []
    
    # Replace common abbreviations temporarily
    text = text.replace('Dr.', 'Dr<DOT>')
    text = text.replace('Mr.', 'Mr<DOT>')
    text = text.replace('Mrs.', 'Mrs<DOT>')
    text = text.replace('Ms. ', 'Ms<DOT>')
    text = text.replace('etc.', 'etc<DOT>')
    text = text.replace('i.e.', 'i<DOT>e<DOT>')
    text = text.replace('e.g.', 'e<DOT>g<DOT>')
    text = text.replace('vs.', 'vs<DOT>')
    text = text.replace('Inc.', 'Inc<DOT>')
    text = text.replace('Ltd.', 'Ltd<DOT>')
    
    # Split on sentence boundaries (period, exclamation, question mark followed by space)
    # Use a simpler regex pattern that's compatible with Python's re module
    sentences = re.split(r'([.!?]+)\s+', text)
    
    # Restore abbreviations
    sentences = [s.replace('<DOT>', '. ').strip() for s in sentences]
    
    # Filter empty sentences
    sentences = [s for s in sentences if s]
    
    return sentences


def count_words(text: str) -> int:
    """Count words in text."""
    if not text: 
        return 0
    return len(text.split())


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for transformer models.
    Rule of thumb: ~0.75 tokens per word for English.  
    """
    word_count = count_words(text)
    return int(word_count * 0.75)