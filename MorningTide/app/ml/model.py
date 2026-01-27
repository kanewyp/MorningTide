"""
model.py - network architecture definitions
"""
import torch
import torch.nn as nn
from transformers import DistilBertModel # type: ignore


class CustomDistilBertForSequenceClassification(nn.Module):
    """
    Custom DistilBERT model for multi-label emotion classification. 
    
    Args:
        num_labels (int): Number of emotion classes (default: 20)
        dropout_rate (float): Dropout probability (default: 0.3)
    """
    
    def __init__(self, num_labels=20, dropout_rate=0.3):
        super(CustomDistilBertForSequenceClassification, self).__init__()
        self.num_labels = num_labels
        
        # Load pre-trained DistilBERT
        self.distilbert = DistilBertModel.from_pretrained('distilbert-base-uncased')
        
        # Classification head
        self.pre_classifier = nn.Linear(768, 768)
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(768, num_labels)
        self.relu = nn.ReLU()
    
    def forward(self, input_ids, attention_mask):
        """
        Forward pass through the model. 
        
        Args:
            input_ids: Tokenized input (batch_size, seq_length)
            attention_mask:  Attention mask (batch_size, seq_length)
            
        Returns: 
            logits: Raw predictions (batch_size, num_labels)
        """
        # Get DistilBERT outputs
        distilbert_output = self.distilbert(
            input_ids=input_ids, 
            attention_mask=attention_mask
        )
        
        # Extract [CLS] token representation
        hidden_state = distilbert_output[0]  # (batch_size, seq_length, 768)
        pooled_output = hidden_state[: , 0]   # (batch_size, 768)
        
        # Pass through classification head
        pooled_output = self.pre_classifier(pooled_output)
        pooled_output = self.relu(pooled_output)
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        return logits
    
    def freeze_distilbert(self):
        """Freeze DistilBERT parameters for transfer learning."""
        for param in self.distilbert. parameters():
            param.requires_grad = False
    
    def unfreeze_distilbert(self):
        """Unfreeze DistilBERT parameters for fine-tuning."""
        for param in self.distilbert.parameters():
            param.requires_grad = True