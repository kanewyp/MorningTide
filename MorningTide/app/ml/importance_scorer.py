import re
from typing import List, Protocol
from abc import ABC, abstractmethod


class ImportanceScorer(ABC):
    """Abstract base class for importance scoring strategies."""
    
    @abstractmethod
    def score(self, sentences: List[str]) -> List[float]:
        """
        Score emotional importance of sentences.
        
        Args:
            sentences: List of sentences to score
            
        Returns: 
            List of importance scores (0-1) for each sentence
        """
        pass


class KeywordImportanceScorer(ImportanceScorer):
    """
    Score importance based on emotion keywords and linguistic patterns.
    Fast, no dependencies, good baseline performance.
    """
    
    def __init__(self):
        # Core emotion words
        self.emotion_words = {
            # Negative emotions
            'angry', 'anger', 'mad', 'furious', 'irritated', 'annoyed',
            'sad', 'sadness', 'depressed', 'miserable', 'unhappy', 'down',
            'anxious', 'anxiety', 'worried', 'nervous', 'stressed', 'tense',
            'afraid', 'fear', 'scared', 'terrified', 'frightened',
            'frustrated', 'frustration', 'annoying', 'irritating',
            'disappointed', 'disappointment', 'letdown',
            'disgusted', 'disgust', 'revolted', 'repulsed',
            'embarrassed', 'embarrassment', 'ashamed', 'humiliated',
            'guilty', 'guilt', 'regret', 'remorse',
            'jealous', 'jealousy', 'envious', 'envy',
            'lonely', 'loneliness', 'isolated', 'alone',
            'confused', 'confusion', 'uncertain', 'bewildered',
            
            # Positive emotions
            'happy', 'happiness', 'joy', 'joyful', 'cheerful', 'delighted',
            'excited', 'excitement', 'thrilled', 'exhilarated',
            'love', 'loving', 'adore', 'cherish', 'affection',
            'grateful', 'gratitude', 'thankful', 'appreciated',
            'proud', 'pride', 'accomplished',
            'relieved', 'relief',
            'hopeful', 'hope', 'optimistic',
            'surprised', 'surprise', 'amazed', 'astonished',
        }
        
        # Intensity modifiers
        self.intensifiers = {
            'very', 'extremely', 'so', 'really', 'incredibly', 'absolutely',
            'totally', 'completely', 'utterly', 'deeply', 'highly',
            'super', 'quite', 'particularly', 'especially', 'remarkably'
        }
        
        # Negations (also emotionally significant)
        self.negations = {
            'not', 'never', 'no', "n't", "don't", "can't", "won't",
            "couldn't", "wouldn't", "shouldn't", 'nobody', 'nothing', 'nowhere'
        }
        
        # Emotional punctuation patterns
        self.exclamation_pattern = re.compile(r'! +')
        self.question_pattern = re.compile(r'\?+')
        self.caps_pattern = re.compile(r'\b[A-Z]{2,}\b')  # ALL CAPS words
    
    def score(self, sentences: List[str]) -> List[float]:
        """Score sentences based on keyword and pattern matching."""
        if not sentences:
            return []
        
        raw_scores = []
        
        for sentence in sentences:
            score = 0.0
            words = set(word.lower().strip('.,!?;:') for word in sentence.split())
            
            # 1. Count emotion words (most important signal)
            emotion_count = len(words & self.emotion_words)
            score += emotion_count * 3.0
            
            # 2. Count intensifiers
            intensifier_count = len(words & self.intensifiers)
            score += intensifier_count * 1.0
            
            # 3. Count negations
            negation_count = len(words & self. negations)
            score += negation_count * 0.8
            
            # 4. Punctuation patterns
            exclamations = len(self.exclamation_pattern.findall(sentence))
            score += exclamations * 1.5
            
            questions = len(self.question_pattern.findall(sentence))
            score += questions * 0.5
            
            caps_words = len(self.caps_pattern.findall(sentence))
            score += caps_words * 1.0
            
            # 5. First-person pronouns (emotional statements often personal)
            first_person = len(words & {'i', "i'm", 'me', 'my', 'mine', 'myself'})
            score += first_person * 0.3
            
            # Normalize by sentence length to avoid bias toward long sentences
            word_count = len(sentence.split())
            if word_count > 0:
                score = score / word_count * 10.0  # Scale up for readability
            
            raw_scores.append(score)
        
        # Normalize to 0-1 range
        max_score = max(raw_scores) if raw_scores else 1.0
        if max_score > 0:
            normalized_scores = [min(s / max_score, 1.0) for s in raw_scores]
        else:
            normalized_scores = [0.0] * len(sentences)
        
        return normalized_scores


class MLImportanceScorer(ImportanceScorer):
    """
    Score importance using a pre-trained emotion detection model.
    More accurate than keywords, still fast and local.
    """
    
    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        """
        Initialize ML-based scorer.
        
        Args:
            model_name: HuggingFace model name for emotion detection
        """
        self.model_name = model_name
        self._pipeline = None  # Lazy loading
    
    def _load_model(self):
        """Lazy load the emotion detection model."""
        if self._pipeline is None:
            try:
                from transformers import pipeline
                import torch
                
                device = 0 if torch.cuda.is_available() else -1
                self._pipeline = pipeline(
                    "text-classification",
                    model=self.model_name,
                    top_k=None,
                    device=device
                )
                print(f"✓ Loaded importance scoring model: {self.model_name}")
            except Exception as e:
                print(f"⚠ Failed to load ML importance scorer: {e}")
                print("  Falling back to keyword-based scoring")
                # Fallback to keyword scorer
                self._fallback_scorer = KeywordImportanceScorer()
    
    def score(self, sentences: List[str]) -> List[float]:
        """Score sentences using emotion detection model."""
        self._load_model()
        
        # Use fallback if model failed to load
        if self._pipeline is None and hasattr(self, '_fallback_scorer'):
            return self._fallback_scorer.score(sentences)
        
        if not sentences:
            return []
        
        try:
            # Batch prediction for efficiency
            predictions = self._pipeline(sentences, batch_size=8)
            
            # Extract importance as max confidence across all emotions
            importance_scores = []
            for pred in predictions:
                # pred is a list of dicts:  [{'label': 'joy', 'score': 0.8}, ...]
                max_confidence = max(p['score'] for p in pred)
                importance_scores.append(max_confidence)
            
            # Normalize to 0-1 range
            max_score = max(importance_scores) if importance_scores else 1.0
            if max_score > 0:
                importance_scores = [s / max_score for s in importance_scores]
            
            return importance_scores
            
        except Exception as e:
            print(f"⚠ Error during ML scoring: {e}")
            # Fallback to keyword scoring
            fallback_scorer = KeywordImportanceScorer()
            return fallback_scorer.score(sentences)


# Factory function for easy scorer creation
def create_importance_scorer(method:  str = "keyword") -> ImportanceScorer:
    """
    Factory function to create importance scorers.
    
    Args:
        method:  Scoring method ("keyword" or "ml")
        
    Returns: 
        ImportanceScorer instance
    """
    if method == "keyword": 
        return KeywordImportanceScorer()
    elif method == "ml":
        return MLImportanceScorer()
    else:
        raise ValueError(f"Unknown importance scoring method: {method}")