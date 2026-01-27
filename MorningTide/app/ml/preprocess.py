from typing import List
import sys
from pathlib import Path
import string

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from app.config import Config # type: ignore
from sklearn.model_selection import train_test_split # type: ignore


class TextPreprocessor:
    """Text preprocessing utilities"""

    @staticmethod
    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.strip()

    @staticmethod
    def batch_clean(texts: List[str]) -> List[str]:
        return [TextPreprocessor.clean_text(text) for text in texts]


def prepare_sentiment_data():
    """
    Prepare sentiment classification dataset
    """
    if train_test_split is None:
        raise ImportError("scikit-learn is required for train_test_split. Install with: pip install scikit-learn")

    # Locate and load the data set
    raw_dir = Path(Config.RAW_DATA_DIR)
    df = pd.read_csv(raw_dir / 'emotion_dataset.csv')

    print(f"Loaded data from: {raw_dir / 'emotion_dataset.csv'}")
    print(f"Loaded {len(df)} samples")
    print(f"Columns: {df.columns.tolist()}")

    # Detect text and label columns
    text_col = 'cleaned_text'
    label_col = 'emotion'

    # Keep only needed columns and normalize names
    df = df[[text_col, label_col]].rename(columns={text_col: 'text', label_col: 'label'})

    # Clean texts (the raw data is already cleaned, batch_clean() will be elaborated once manual data collection is done)
    df['text'] = TextPreprocessor.batch_clean(df['text'].astype(str).tolist())

    # Remove short/empty texts
    df = df[df['text'].str.len() > 3]
    print(f"After cleaning, {len(df)} samples remain")

    # Ensure processed dir exists
    processed_dir = Path(Config.PROCESSED_DATA_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Stratify if possible
    stratify_col = None
    try:
        vc = df['label'].value_counts()
        if len(vc) > 1 and (vc >= 2).all():
            stratify_col = df['label']
    except Exception:
        stratify_col = None

    # Split
    try:
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=stratify_col)
    except Exception:
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    # Save processed data
    train_df.to_csv(processed_dir / 'train.csv', index=False)
    val_df.to_csv(processed_dir / 'validation.csv', index=False)

    print(f"✓ Saved {len(train_df)} training samples")
    print(f"✓ Saved {len(val_df)} validation samples")

    return train_df, val_df


def preprocess_for_inference(text:  str) -> str:
    """
    Preprocess text for inference by lowercasing and removing punctuation (except apostrophes).
    
    Args:
        text: Raw input text (journal entry)
        
    Returns:
        Preprocessed text (lowercased, no punctuation except apostrophes)
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except apostrophes
    punctuation_to_remove = string.punctuation. replace("'", "")
    text = text.translate(str.maketrans('', '', punctuation_to_remove))
    
    # Remove extra whitespace (multiple spaces to single space)
    text = ' '.join(text.split())
    
    return text.strip()


if __name__ == '__main__':
    print('=' * 50)
    print('PREPARING SENTIMENT DATA')
    print('=' * 50)
    prepare_sentiment_data()
