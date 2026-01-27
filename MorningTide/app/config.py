"""
config.py - Centralized configuration for MorningTide project
"""

import os
import torch
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Config:   
    """Application configuration for MorningTide emotion classification"""
    
    # ========== Base Directories ==========
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    MODELS_DIR = BASE_DIR / 'models'
    ML_DIR = BASE_DIR / 'ml'
    
    # Data directories
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'
    
    # Model directories
    SENTIMENT_MODEL_DIR = MODELS_DIR / 'sentiment'
    MOOD_TEMP_MODEL_DIR = MODELS_DIR / 'intensity'
    CHECKPOINT_DIR = BASE_DIR / 'checkpoints'
    
    # ========== Dataset Settings ==========
    TRAIN_CSV = PROCESSED_DATA_DIR / 'train.csv'
    VAL_CSV = PROCESSED_DATA_DIR / 'validation.csv'
    TEST_CSV = PROCESSED_DATA_DIR / 'test.csv'  # If you have one
    
    # Dataset column names
    TEXT_COLUMN = 'text'
    LABEL_COLUMN = 'label'
    
    # ========== Model Architecture Settings ==========
    MODEL_NAME = 'distilbert-base-uncased'
    NUM_LABELS = 20  # Number of emotion classes
    DROPOUT_RATE = 0.3
    HIDDEN_SIZE = 768  # DistilBERT hidden size
    
    # ========== Training Hyperparameters ==========
    # Data loading
    BATCH_SIZE = 16
    NUM_WORKERS = 0  # Set to 0 for Windows, 2-4 for Linux/Mac
    PIN_MEMORY = True if torch.cuda.is_available() else False
    
    # Tokenization
    MAX_LENGTH = 512  # Maximum sequence length
    TRUNCATION = True
    PADDING = 'max_length'
    
    # Optimization
    LEARNING_RATE = 5e-5
    WEIGHT_DECAY = 0.01
    ADAM_EPSILON = 1e-8
    MAX_GRAD_NORM = 1.0  # Gradient clipping
    
    # Training loop
    NUM_EPOCHS = 10
    WARMUP_STEPS = 0  # Number of warmup steps for learning rate scheduler
    LOG_INTERVAL = 100  # Log every N batches
    EVAL_INTERVAL = 1  # Evaluate every N epochs
    SAVE_TOTAL_LIMIT = 3  # Keep only the last N checkpoints
    
    # Early stopping
    EARLY_STOPPING_PATIENCE = 3  # Stop if no improvement for N epochs
    EARLY_STOPPING_MIN_DELTA = 0.001  # Minimum change to qualify as improvement
    
    # ========== Long Text Handling Settings ==========
    # Adaptive analysis for long journal entries
    ADAPTIVE_ANALYSIS_ENABLED = True
    SHORT_TEXT_THRESHOLD = 30  # words - texts shorter than this use direct classification
    MIN_SENTENCE_LENGTH = 5  # characters - minimum sentence length to analyze
    DEFAULT_IMPORTANCE_METHOD = "ml"  # "keyword" or "ml"
    
    # ML importance scorer settings (used when DEFAULT_IMPORTANCE_METHOD = "ml")
    IMPORTANCE_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
    IMPORTANCE_BATCH_SIZE = 8  # Batch size for importance scoring
    
    # ========== Device Settings ==========
    # Priority:   Intel XPU > CUDA > CPU
    if hasattr(torch, 'xpu') and torch.xpu. is_available():
        DEVICE = 'xpu'  # Intel Arc Graphics
        os.environ['SYCL_DEVICE_FILTER'] = 'level_zero'
    elif torch.cuda.is_available():
        DEVICE = 'cuda'  # NVIDIA GPU
    else:
        DEVICE = 'cpu'

    CUDA_VISIBLE_DEVICES = os.getenv('CUDA_VISIBLE_DEVICES', '0')
    XPU_VISIBLE_DEVICES = os.getenv('XPU_VISIBLE_DEVICES', '0')
    
    # Mixed precision training (speeds up training on modern GPUs)
    USE_AMP = torch.cuda.is_available()  # Automatic Mixed Precision
    
    # ========== Reproducibility ==========
    RANDOM_SEED = 42
    
    # ========== Logging & Checkpointing ==========
    SAVE_BEST_ONLY = False  # Save all checkpoints or only the best
    SAVE_OPTIMIZER_STATE = True  # Include optimizer state in checkpoints
    CHECKPOINT_FILENAME = 'model_epoch_{epoch}.pt'
    BEST_MODEL_FILENAME = 'best_model.pt'
    LATEST_MODEL_FILENAME = 'latest_model.pt'
    HISTORY_FILENAME = 'training_history.json'
    
    # ========== Evaluation Settings ==========
    EVAL_BATCH_SIZE = 32  # Can be larger than training batch size
    SAVE_PREDICTIONS = True  # Save predictions to CSV
    PREDICTIONS_FILENAME = 'predictions.csv'
    
    # ========== API Settings ==========
    HOST = '0.0.0.0'
    PORT = 8000
    DEBUG = True
    
    # ========== Emotion Mapping ==========
    EMOTION_MAPPING = {
        'anger': 0,
        'anxiety': 1,
        'confusion': 2,
        'disappointment': 3,
        'disgust': 4,
        'embarrassment': 5,
        'excitement': 6,
        'fear': 7,
        'frustration': 8,
        'gratitude': 9,
        'guilt': 10,
        'happiness': 11,
        'hope': 12,
        'jealousy': 13,
        'loneliness': 14,
        'love': 15,
        'pride': 16,
        'relief': 17,
        'sadness': 18,
        'surprise': 19
    }
    
    ID_TO_EMOTION = {v: k for k, v in EMOTION_MAPPING.items()}
    
    # ==================== RAG Configuration (NEW) ====================
    # Ollama Settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    OLLAMA_NUM_PREDICT = int(os. getenv("OLLAMA_NUM_PREDICT", "512"))

    # Embedding Settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

    # Vector Store Settings
    VECTOR_STORE_PATH = os.getenv(
        "VECTOR_STORE_PATH",
        str(DATA_DIR / "vector_store")
    )
    VECTOR_STORE_DIMENSION = int(os.getenv("VECTOR_STORE_DIMENSION", "384"))

    # RAG Settings
    RAG_CONTEXT_WINDOW = int(os. getenv("RAG_CONTEXT_WINDOW", "4096"))
    RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    RAG_CHUNK_OVERLAP = int(os. getenv("RAG_CHUNK_OVERLAP", "64"))
    RAG_TOP_K_RETRIEVAL = int(os.getenv("RAG_TOP_K_RETRIEVAL", "5"))
    RAG_CORPUS_PATH = os.getenv(
        "RAG_CORPUS_PATH",
        str(DATA_DIR / "therapy_corpus" / "seed_corpus.json")
    )
    
    # ========== Methods ==========
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.SENTIMENT_MODEL_DIR,
            cls. MOOD_TEMP_MODEL_DIR,
            cls. CHECKPOINT_DIR,
            cls.DATA_DIR / "therapy_corpus",
            cls.DATA_DIR / "vector_store",
        ]
        
        print("Creating project directories...")
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {directory. relative_to(cls.BASE_DIR)}")
        print()
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("=" * 80)
        print("MorningTide Configuration")
        print("=" * 80)
        print(f"\n📁 Directories:")
        print(f"  Base:          {cls.BASE_DIR}")
        print(f"  Data:         {cls.DATA_DIR}")
        print(f"  Checkpoints:   {cls.CHECKPOINT_DIR}")
        
        print(f"\n📊 Dataset:")
        print(f"  Train CSV:    {cls. TRAIN_CSV}")
        print(f"  Val CSV:      {cls.VAL_CSV}")
        print(f"  Text column:  {cls.TEXT_COLUMN}")
        print(f"  Label column:   {cls.LABEL_COLUMN}")
        
        print(f"\n🤖 Model:")
        print(f"  Architecture: {cls.MODEL_NAME}")
        print(f"  Num labels:   {cls.NUM_LABELS}")
        print(f"  Dropout:      {cls.DROPOUT_RATE}")
        print(f"  Max length:   {cls.MAX_LENGTH}")
        
        print(f"\n⚙️  Training:")
        print(f"  Batch size:   {cls.BATCH_SIZE}")
        print(f"  Epochs:        {cls.NUM_EPOCHS}")
        print(f"  Learning rate: {cls.LEARNING_RATE}")
        print(f"  Weight decay:  {cls.WEIGHT_DECAY}")
        print(f"  Max grad norm: {cls.MAX_GRAD_NORM}")
        
        print(f"\n📝 Long Text Handling:")
        print(f"  Adaptive analysis: {cls.ADAPTIVE_ANALYSIS_ENABLED}")
        print(f"  Short text threshold:   {cls.SHORT_TEXT_THRESHOLD} words")
        print(f"  Importance method: {cls.DEFAULT_IMPORTANCE_METHOD}")
        if cls.DEFAULT_IMPORTANCE_METHOD == "ml": 
            print(f"  Importance model: {cls.IMPORTANCE_MODEL_NAME}")
        
        print(f"\n🧠 RAG Configuration:")
        print(f"  Ollama URL:   {cls.OLLAMA_BASE_URL}")
        print(f"  Ollama Model: {cls.OLLAMA_MODEL}")
        print(f"  Embedding:     {cls.EMBEDDING_MODEL}")
        print(f"  Device:       {cls.EMBEDDING_DEVICE}")
        print(f"  Vector Store: {cls.VECTOR_STORE_PATH}")
        print(f"  Corpus Path:   {cls.RAG_CORPUS_PATH}")
        
        print(f"\n💻 Device:")
        print(f"  Device:        {cls.DEVICE}")
        if cls. DEVICE == 'cuda':  
            print(f"  GPU:           {torch.cuda.get_device_name(0)}")
            print(f"  Mixed precision: {cls.USE_AMP}")
        
        print(f"\n🎲 Reproducibility:")
        print(f"  Random seed:  {cls.RANDOM_SEED}")
        print("=" * 80)
        print()
    
    @classmethod
    def set_seed(cls):
        """Set random seeds for reproducibility"""
        import random
        import numpy as np
        
        random.seed(cls.RANDOM_SEED)
        np.random.seed(cls.RANDOM_SEED)
        torch.manual_seed(cls. RANDOM_SEED)
        
        if torch.cuda.is_available():
            torch.cuda.manual_seed(cls.RANDOM_SEED)
            torch.cuda.manual_seed_all(cls.RANDOM_SEED)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        
        print(f"✓ Random seed set to {cls. RANDOM_SEED} for reproducibility\n")
    
    @classmethod
    def get_device_info(cls):
        """Get detailed device information"""
        if cls.DEVICE == 'cuda':  
            return {
                'device':   'cuda',
                'gpu_name': torch.cuda.get_device_name(0),
                'gpu_count': torch.cuda.device_count(),
                'cuda_version': torch.version.cuda,
                'memory_allocated':  f"{torch.cuda.memory_allocated(0) / 1e9:.2f} GB",
                'memory_total': f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
            }
        else:
            return {
                'device':  'cpu',
                'cpu_count':   os.cpu_count()
            }


# Run on import
Config.create_directories()