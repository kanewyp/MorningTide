"""
inference.py - Load trained model and perform inference
This is used by the API to analyze journal entries in real-time. 

Updated to support both direct and adaptive analysis. 
"""

import torch
from transformers import DistilBertTokenizerFast
from pathlib import Path
from typing import Dict, List
import numpy as np

from app.ml.model import CustomDistilBertForSequenceClassification
from app. ml.preprocess import preprocess_for_inference
from app.config import Config


class EmotionClassifier:
    """
    Singleton class for emotion classification.
    Loads the model once and reuses it for all predictions.  
    
    This class handles core emotion classification for single, preprocessed inputs.
    For long text handling, see long_text_handler.py
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        self._initialized = True
        
        # Load model on initialization
        self. load_model()
    
    def load_model(self, checkpoint_path: str = None):
        """
        Load the trained model from checkpoint.
        
        Args:
            checkpoint_path: Path to model checkpoint (defaults to best_model.pt)
        """
        if checkpoint_path is None: 
            checkpoint_path = Config. CHECKPOINT_DIR / Config.BEST_MODEL_FILENAME
        
        checkpoint_path = Path(checkpoint_path)
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Model checkpoint not found at {checkpoint_path}. "
                f"Please train the model first by running: python app/ml/train.py"
            )
        
        print(f"Loading model from {checkpoint_path}...")
        
        # Load tokenizer
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(Config.MODEL_NAME)
        
        # Load model
        self.model = CustomDistilBertForSequenceClassification(
            num_labels=Config.NUM_LABELS,
            dropout_rate=Config.DROPOUT_RATE
        )
        
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"✓ Model loaded successfully on {self.device}")

    def _get_emotion_valence_scores(self) -> Dict[str, float]:  
        """
        Define valence scores for each emotion.
        
        Valence scale: 
        - Highly negative emotions:  -1.0 to -0.7
        - Moderately negative emotions: -0.7 to -0.4
        - Mildly negative emotions: -0.4 to -0.1
        - Neutral emotions: -0.1 to 0.1
        - Mildly positive emotions: 0.1 to 0.4
        - Moderately positive emotions: 0.4 to 0.7
        - Highly positive emotions: 0.7 to 1.0
    
        Returns:  
            Dictionary mapping emotion names to valence scores
        """
        return {
            # Highly negative emotions (-1.0 to -0.7)
            'disgust': -0.95,
            'anger': -0.85,
            'fear': -0.80,
            'sadness': -0.75,
        
            # Moderately negative emotions (-0.7 to -0.4)
            'guilt': -0.70,
            'anxiety': -0.65,
            'loneliness': -0.60,
            'frustration': -0.55,
            'jealousy': -0.50,
            'embarrassment': -0.45,
        
            # Mildly negative emotions (-0.4 to -0.1)
            'disappointment': -0.40,
            'confusion': -0.20,
        
            # Neutral to mildly positive (0.0 to 0.4)
            'surprise': 0.10,
            'relief': 0.35,
        
            # Moderately positive emotions (0.4 to 0.7)
            'hope': 0.50,
            'gratitude': 0.65,
            'pride': 0.70,
        
            # Highly positive emotions (0.7 to 1.0)
            'excitement': 0.75,
            'happiness': 0.85,
            'love': 0.90,
        }
    
    def _calculate_emotional_intensity(self, probabilities: np.ndarray) -> float:
        """
        Calculate emotional intensity score from 1-10 based on valence-weighted probabilities.
    
        Args:
            probabilities:  Numpy array of softmax probabilities for all emotions
        
        Returns:  
            Emotional intensity score from 1 (very negative) to 10 (very positive)
        """
        valence_scores = self._get_emotion_valence_scores()
        weighted_valence = 0.0
        
        for idx, prob in enumerate(probabilities):
            emotion_name = Config.ID_TO_EMOTION[idx]
            valence = valence_scores. get(emotion_name, 0.0)
            weighted_valence += prob * valence
        
        # Map from [-1, 1] to [1, 10]
        emotional_intensity = (weighted_valence + 1) * 4.5 + 1
        emotional_intensity = np.clip(emotional_intensity, 1.0, 10.0)
        
        return emotional_intensity

    def predict(self, text: str) -> Dict: 
        """
        Predict emotion for a single text.  
        Returns top 3 emotions with probabilities and emotional intensity score.
        
        Note: This method performs direct classification without text length adaptation.
        For automatic handling of long texts, use analyze_emotion() from this module.
        
        Args:
            text: Input text (journal entry)
            
        Returns:  
            Dictionary with prediction results
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Preprocess text
        cleaned_text = preprocess_for_inference(text)
        
        if not cleaned_text:
            return {
                'top_emotion': 'unknown',
                'top_confidence': 0.0,
                'top_3_emotions':  [],
                'all_scores':  {},
                'emotional_intensity':  5.0,
                'cleaned_text': '',
                'error': 'Empty text after preprocessing'
            }
        
        # Tokenize
        encoding = self.tokenizer. encode_plus(
            cleaned_text,
            add_special_tokens=True,
            max_length=Config.MAX_LENGTH,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probabilities = torch.softmax(logits, dim=1)
            probabilities_np = probabilities[0].cpu().numpy()
        
        # Get all emotion scores
        all_scores = {}
        for idx, score in enumerate(probabilities_np):
            emotion_name = Config. ID_TO_EMOTION[idx]
            all_scores[emotion_name] = float(score)
        
        # Sort by score and get top 3
        sorted_emotions = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = [
            {'emotion': emotion, 'confidence':  float(score)}
            for emotion, score in sorted_emotions[:3]
        ]
        
        # Calculate emotional intensity
        emotional_intensity = self._calculate_emotional_intensity(probabilities_np)
        
        result = {
            'top_emotion': top_3[0]['emotion'],
            'top_confidence':  top_3[0]['confidence'],
            'top_3_emotions': top_3,
            'all_scores': dict(sorted_emotions),
            'emotional_intensity': float(emotional_intensity),
            'cleaned_text': cleaned_text
        }
        
        return result
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """
        Predict emotions for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns: 
            List of prediction dictionaries
        """
        return [self.predict(text) for text in texts]
    
    def get_top_k_emotions(self, text: str, k: int = 3) -> List[Dict]:
        """
        Get top K most likely emotions. 
        
        Args:
            text: Input text
            k:  Number of top emotions to return
            
        Returns:
            List of dictionaries with emotion and confidence
        """
        result = self.predict(text)
        return result['top_3_emotions'][: k]


# Create singleton instance
emotion_classifier = EmotionClassifier()


# ============================================================================
# PUBLIC API - Use these functions in your application
# ============================================================================

def analyze_emotion(text: str, adaptive: bool = True, importance_method: str = "keyword") -> Dict:
    """
    Analyze emotion in text with optional adaptive processing for long texts.
    
    This is the recommended function for general use. 
    
    Args:
        text: Input text (journal entry)
        adaptive: If True, automatically use appropriate method for text length
        importance_method: "keyword" or "ml" (only used if adaptive=True and text is long)
    
    Returns:
        Emotion analysis results
        
    Examples:
        >>> # Short text - direct classification
        >>> result = analyze_emotion("I'm so happy today!")
        
        >>> # Long text - adaptive processing with keyword importance
        >>> result = analyze_emotion(long_journal_entry, adaptive=True, importance_method="keyword")
        
        >>> # Long text - adaptive processing with ML importance (more accurate)
        >>> result = analyze_emotion(long_journal_entry, adaptive=True, importance_method="ml")
    """
    if not adaptive:
        # Direct classification (original behavior)
        return emotion_classifier.predict(text)
    
    # Adaptive processing
    from app.ml.long_text_handler import get_adaptive_analyzer
    analyzer = get_adaptive_analyzer(importance_method=importance_method)
    return analyzer.analyze(text)


def get_top_emotions(text: str, k: int = 3, adaptive: bool = True) -> List[Dict]:
    """
    Get top K emotions (convenience function).
    
    Args:
        text: Input text
        k: Number of top emotions
        adaptive: Use adaptive processing for long texts
        
    Returns:
        List of top K emotions with confidences
    """
    result = analyze_emotion(text, adaptive=adaptive)
    return result['top_3_emotions'][:k]


def get_emotional_intensity(text: str, adaptive: bool = True) -> float:
    """
    Get emotional intensity score (1-10).
    
    Args:
        text: Input text
        adaptive: Use adaptive processing for long texts
        
    Returns:  
        Emotional intensity from 1 (very negative) to 10 (very positive)
    """
    result = analyze_emotion(text, adaptive=adaptive)
    return result['emotional_intensity']


# Backward compatibility aliases
def analyze_emotion_legacy(text: str) -> Dict:
    """Legacy function - always uses direct classification."""
    return emotion_classifier.predict(text)