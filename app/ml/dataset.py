import os
import sys
import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import DistilBertTokenizerFast # type: ignore
from typing import Dict, Optional


class EmotionDataset(Dataset):
    """
    PyTorch Dataset for emotion classification from CSV files.
    
    Args:
        csv_path: Path to CSV file (train.csv or validation.csv)
        tokenizer: Hugging Face tokenizer
        max_length: Maximum sequence length for tokenization
        text_column: Name of the column containing text data
        label_column: Name of the column containing emotion labels
    """
    
    def __init__(
        self, 
        csv_path: str,
        tokenizer: DistilBertTokenizerFast,
        max_length: int = 512,
        text_column: str = 'text',
        label_column: str = 'label'
    ):
        self.csv_path = csv_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.text_column = text_column
        self.label_column = label_column
        
        # Load CSV file
        print(f"Loading dataset from: {csv_path}")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.df = pd.read_csv(csv_path)
        print(f"Loaded {len(self.df)} samples from {os.path.basename(csv_path)}")
        
        # Validate columns
        if text_column not in self.df.columns:
            raise ValueError(f"Text column '{text_column}' not found in CSV.  Available columns: {self.df.columns.tolist()}")
        if label_column not in self.df.columns:
            raise ValueError(f"Label column '{label_column}' not found in CSV. Available columns: {self.df.columns.tolist()}")
        
        # Emotion to ID mapping
        self.emotion_mapping = {
            'anger': 0,
            'anxiety': 1,
            'confusion': 2,
            'disappointment': 3,
            'disgust': 4,
            'embarrassment':  5,
            'excitement':  6,
            'fear':  7,
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
        
        # Verify all emotions in dataset are valid
        unique_emotions = self.df[label_column].unique()
        invalid_emotions = [e for e in unique_emotions if e not in self.emotion_mapping]
        if invalid_emotions:
            raise ValueError(f"Invalid emotions found in dataset: {invalid_emotions}")
        
        print(f"Unique emotions in dataset: {len(unique_emotions)}")
        print(f"Emotion distribution:\n{self.df[label_column].value_counts()}")

    def __len__(self) -> int:
        """Return the total number of samples."""
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]: 
        """
        Get a single sample from the dataset.
        
        Args:
            idx: Index of the sample
            
        Returns:
            Dictionary containing:
                - text: Original text string
                - input_ids:  Tokenized input IDs
                - attention_mask: Attention mask
                - labels:  Emotion label as integer
        """
        # Get text and emotion from DataFrame
        row = self.df.iloc[idx]
        text = str(row[self.text_column])
        emotion = row[self.label_column]
        
        # Convert emotion to numerical label
        label = self.emotion_mapping[emotion]

        # Tokenize the text
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
            truncation=True
        )

        return {
            'text':  text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask':  encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }
    
    def get_emotion_counts(self) -> pd.Series:
        """Get the count of each emotion in the dataset."""
        return self. df[self.label_column]. value_counts()
    
    def get_emotion_mapping(self) -> Dict[str, int]:
        """Get the emotion to ID mapping."""
        return self. emotion_mapping
    
    def get_id_to_emotion_mapping(self) -> Dict[int, str]:
        """Get the ID to emotion mapping."""
        return {v: k for k, v in self.emotion_mapping.items()}


def load_csv_datasets(
    train_csv_path: str,
    val_csv_path: str,
    tokenizer: Optional[DistilBertTokenizerFast] = None,
    max_length: int = 512,
    text_column:  str = 'text',
    label_column: str = 'label'
) -> tuple:
    """
    Load train and validation datasets from CSV files. 
    
    Args:
        train_csv_path: Path to training CSV file
        val_csv_path: Path to validation CSV file
        tokenizer:  Hugging Face tokenizer (if None, will load default)
        max_length: Maximum sequence length
        text_column:  Name of text column in CSV
        label_column: Name of label column in CSV
        
    Returns:
        Tuple of (train_dataset, val_dataset, tokenizer)
    """
    # Load tokenizer if not provided
    if tokenizer is None:
        print("Loading default tokenizer:  distilbert-base-uncased")
        tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    
    # Create datasets
    train_dataset = EmotionDataset(
        csv_path=train_csv_path,
        tokenizer=tokenizer,
        max_length=max_length,
        text_column=text_column,
        label_column=label_column
    )
    
    val_dataset = EmotionDataset(
        csv_path=val_csv_path,
        tokenizer=tokenizer,
        max_length=max_length,
        text_column=text_column,
        label_column=label_column
    )
    
    return train_dataset, val_dataset, tokenizer


def inspect_csv_file(csv_path: str):
    """
    Inspect a CSV file to understand its structure.
    
    Args:
        csv_path: Path to CSV file
    """
    print(f"\n{'='*80}")
    print(f"Inspecting CSV file: {csv_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found!")
        return
    
    df = pd.read_csv(csv_path)
    
    print(f"\nShape:  {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nData types:")
    print(df.dtypes)
    print(f"\nNull values:")
    print(df.isnull().sum())
    
    # If emotion column exists, show distribution
    if 'emotion' in df.columns:
        print(f"\nEmotion distribution:")
        print(df['emotion'].value_counts())
    
    print(f"\n{'='*80}\n")




# Example usage and testing
if __name__ == "__main__":
    # Define paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    TRAIN_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'train.csv')
    VAL_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'validation.csv')
    
    print("MorningTide Dataset Loader - Testing")
    print("="*80)
    
    # Inspect CSV files
    print("\n1. Inspecting CSV files...")
    inspect_csv_file(TRAIN_CSV)
    inspect_csv_file(VAL_CSV)
    
    # Load datasets
    try:
        print("\n2. Loading datasets...")
        train_dataset, val_dataset, tokenizer = load_csv_datasets(
            train_csv_path=TRAIN_CSV,
            val_csv_path=VAL_CSV
        )
        
        print(f"\n✓ Successfully loaded datasets!")
        print(f"  Training samples: {len(train_dataset)}")
        print(f"  Validation samples: {len(val_dataset)}")
        
        # Test getting a sample
        print("\n3. Testing dataset access...")
        sample = train_dataset[0]
        print(f"\nSample data point:")
        print(f"  Text: {sample['text'][: 100]}...")
        print(f"  Label: {sample['labels']. item()}")
        print(f"  Input IDs shape: {sample['input_ids']. shape}")
        print(f"  Attention mask shape: {sample['attention_mask']. shape}")
        
        # Decode tokens
        print(f"\n  Decoded tokens (first 50):")
        decoded = tokenizer.decode(sample['input_ids'][:50])
        print(f"  {decoded}")
        
        # Show emotion mappings
        print(f"\n4. Emotion mappings:")
        id2emotion = train_dataset.get_id_to_emotion_mapping()
        for idx, emotion in sorted(id2emotion.items()):
            print(f"  {idx: 2d}: {emotion}")
        
        print("\n" + "="*80)
        print("✓ All tests passed!")
        
    except Exception as e: 
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()