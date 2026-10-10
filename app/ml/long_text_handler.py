import numpy as np
from typing import Dict, List
from collections import defaultdict

from app.ml.inference import EmotionClassifier
from app. ml.importance_scorer import ImportanceScorer, create_importance_scorer
from app.ml.utils import split_into_sentences, count_words
from app.config import Config


class AdaptiveEmotionAnalyzer:
    """
    Adaptive emotion analyzer that handles both short and long texts intelligently.
    
    For short texts:  Direct classification
    For long texts: Importance-weighted sentence-level analysis
    """
    
    def __init__(
        self,
        emotion_classifier: EmotionClassifier,
        importance_method: str = "keyword",
        short_text_threshold: int = 150,  # words
        min_sentence_length: int = 10,  # characters
    ):
        """
        Initialize adaptive analyzer.
        
        Args:
            emotion_classifier: Trained emotion classifier instance
            importance_method: "keyword" or "ml" for importance scoring
            short_text_threshold: Word count threshold for short vs long text
            min_sentence_length:  Minimum sentence length to analyze (chars)
        """
        self.emotion_classifier = emotion_classifier
        self.short_text_threshold = short_text_threshold
        self.min_sentence_length = min_sentence_length
        
        # Create importance scorer
        self.importance_scorer = create_importance_scorer(importance_method)
        
        print(f"✓ Adaptive analyzer initialized (method: {importance_method})")
    
    def analyze(self, text: str, force_method: str = None) -> Dict:
        """
        Analyze emotion in text with adaptive strategy.
        
        Args:
            text: Input journal entry
            force_method: Force specific method ("short" or "long"), None for auto
            
        Returns:
            Emotion analysis results
        """
        if not text or not text.strip():
            return self._empty_result()
        
        word_count = count_words(text)
        
        # Determine method
        if force_method == "short" or (force_method is None and word_count < self.short_text_threshold):
            return self._analyze_short_text(text, word_count)
        else:
            return self._analyze_long_text(text, word_count)
    
    def _analyze_short_text(self, text: str, word_count: int) -> Dict:
        """Direct classification for short texts."""
        result = self.emotion_classifier.predict(text)
        result['method'] = 'direct'
        result['word_count'] = word_count
        result['num_sentences'] = 1
        return result
    
    def _analyze_long_text(self, text: str, word_count: int) -> Dict:
        """Importance-weighted analysis for long texts."""
        # 1. Split into sentences
        sentences = split_into_sentences(text)
        
        if not sentences:
            return self._empty_result()
        
        # 2. Filter very short sentences
        valid_sentences = [s for s in sentences if len(s) >= self.min_sentence_length]
        
        if not valid_sentences:
            # Fall back to direct classification if no valid sentences
            return self._analyze_short_text(text, word_count)
        
        # 3. Score importance
        importance_scores = self.importance_scorer.score(valid_sentences)
        
        # 4. Analyze each sentence
        sentence_results = []
        for sentence, importance in zip(valid_sentences, importance_scores):
            try:
                result = self. emotion_classifier.predict(sentence)
                sentence_results.append({
                    'sentence': sentence,
                    'importance': importance,
                    'emotions': result['all_scores'],
                    'intensity': result['emotional_intensity'],
                    'top_emotion': result['top_emotion'],
                    'top_confidence': result['top_confidence']
                })
            except Exception as e:
                print(f"⚠ Error analyzing sentence: {e}")
                continue
        
        if not sentence_results:
            # Fallback to direct classification
            return self._analyze_short_text(text, word_count)
        
        # 5. Aggregate results
        aggregated = self._weighted_aggregate(sentence_results)
        
        # 6. Add metadata
        aggregated['method'] = 'importance_weighted'
        aggregated['word_count'] = word_count
        aggregated['num_sentences'] = len(sentence_results)
        aggregated['sentence_details'] = [
            {
                'sentence':  r['sentence'][:100],  # Truncate for display
                'importance': round(r['importance'], 3),
                'emotion': r['top_emotion'],
                'confidence': round(r['top_confidence'], 3)
            }
            for r in sentence_results[: 5]  # Top 5 for brevity
        ]
        
        return aggregated
    
    def _weighted_aggregate(self, sentence_results: List[Dict]) -> Dict:
        """
        Aggregate emotion predictions weighted by importance scores.
        
        Args:
            sentence_results: List of per-sentence analysis results
            
        Returns: 
            Aggregated emotion analysis
        """
        # Normalize importance weights
        total_importance = sum(r['importance'] for r in sentence_results)
        if total_importance == 0:
            weights = [1.0 / len(sentence_results)] * len(sentence_results)
        else:
            weights = [r['importance'] / total_importance for r in sentence_results]
        
        # Weighted sum of emotion probabilities
        aggregated_emotions = defaultdict(float)
        for result, weight in zip(sentence_results, weights):
            for emotion, prob in result['emotions'].items():
                aggregated_emotions[emotion] += prob * weight
        
        # Sort and get top 3
        sorted_emotions = sorted(
            aggregated_emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_3 = [
            {'emotion': emotion, 'confidence': float(score)}
            for emotion, score in sorted_emotions[:3]
        ]
        
        # Weighted average intensity
        weighted_intensity = sum(
            r['intensity'] * w
            for r, w in zip(sentence_results, weights)
        )
        
        # Construct cleaned text (join sentences)
        cleaned_text = ' '. join(r['sentence'] for r in sentence_results)
        
        return {
            'top_emotion': top_3[0]['emotion'],
            'top_confidence':  top_3[0]['confidence'],
            'top_3_emotions': top_3,
            'all_scores': dict(sorted_emotions),
            'emotional_intensity': float(weighted_intensity),
            'cleaned_text': cleaned_text[: 500]  # Truncate for API response
        }
    
    def _empty_result(self) -> Dict:
        """Return empty/neutral result for invalid inputs."""
        return {
            'top_emotion': 'unknown',
            'top_confidence':  0.0,
            'top_3_emotions': [],
            'all_scores': {},
            'emotional_intensity': 5.0,
            'cleaned_text': '',
            'method': 'empty',
            'word_count': 0,
            'num_sentences': 0,
            'error':  'Empty or invalid text'
        }


# Singleton instance (lazy loaded)
_adaptive_analyzer = None


def get_adaptive_analyzer(importance_method: str = "keyword") -> AdaptiveEmotionAnalyzer:
    """
    Get or create singleton adaptive analyzer.
    
    Args:
        importance_method: "keyword" or "ml"
        
    Returns:
        AdaptiveEmotionAnalyzer instance
    """
    global _adaptive_analyzer
    
    if _adaptive_analyzer is None:
        from app.ml.inference import emotion_classifier
        _adaptive_analyzer = AdaptiveEmotionAnalyzer(
            emotion_classifier=emotion_classifier,
            importance_method=importance_method
        )
    
    return _adaptive_analyzer