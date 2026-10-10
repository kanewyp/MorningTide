import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from tqdm import tqdm
import json

import sys
from pathlib import Path

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parent.parent))

from model import CustomDistilBertForSequenceClassification
from dataset import load_csv_datasets
from config import Config


class Trainer:
    """Handles model training and validation."""
    
    def __init__(
        self,
        model,
        train_loader,
        val_loader,
        optimizer,
        device,
        config
    ):
        self.model = model
        self.train_loader = train_loader
        self. val_loader = val_loader
        self.optimizer = optimizer
        self.device = device
        self.config = config
        self.criterion = nn.CrossEntropyLoss()
        
        # Create checkpoint directory
        config.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Track training history
        self.history = {
            'train_losses': [],
            'val_losses': [],
            'val_accuracies': [],
            'learning_rates': []
        }
        
        self.best_val_loss = float('inf')
        self.best_val_accuracy = 0.0
        self.epochs_without_improvement = 0
    
    def train_epoch(self, epoch):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        num_batches = len(self.train_loader)
        
        progress_bar = tqdm(
            self.train_loader, 
            desc=f"Epoch {epoch + 1}/{self.config.NUM_EPOCHS} [Train]",
            ncols=100
        )
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move data to device
            input_ids = batch['input_ids'].to(self. device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask)
            loss = self.criterion(logits, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(), 
                max_norm=self.config.MAX_GRAD_NORM
            )
            
            self.optimizer.step()
            
            # Update metrics
            total_loss += loss. item()
            current_avg_loss = total_loss / (batch_idx + 1)
            
            # Update progress bar
            progress_bar. set_postfix({
                'loss': f'{loss.item():.4f}',
                'avg':  f'{current_avg_loss:.4f}'
            })
            
            # Log periodically
            if (batch_idx + 1) % self.config.LOG_INTERVAL == 0:
                print(f"\n  → Batch {batch_idx + 1}/{num_batches} | "
                      f"Loss: {loss.item():.4f} | "
                      f"Avg:  {current_avg_loss:.4f}")
        
        avg_epoch_loss = total_loss / num_batches
        self.history['train_losses'].append(avg_epoch_loss)
        self.history['learning_rates'].append(self.optimizer.param_groups[0]['lr'])
        
        return avg_epoch_loss
    
    def validate(self):
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        progress_bar = tqdm(
            self.val_loader, 
            desc="Validating",
            ncols=100
        )
        
        with torch.no_grad():
            for batch in progress_bar:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                logits = self.model(input_ids=input_ids, attention_mask=attention_mask)
                loss = self.criterion(logits, labels)
                
                # Calculate accuracy
                predictions = torch.argmax(logits, dim=1)
                correct += (predictions == labels).sum().item()
                total += labels. size(0)
                total_loss += loss.item()
                
                # Update progress bar
                current_accuracy = correct / total if total > 0 else 0
                progress_bar.set_postfix({'acc': f'{current_accuracy:.4f}'})
        
        avg_loss = total_loss / len(self.val_loader)
        accuracy = correct / total
        
        self.history['val_losses'].append(avg_loss)
        self.history['val_accuracies'].append(accuracy)
        
        return avg_loss, accuracy
    
    def check_early_stopping(self, val_accuracy):
        """Check if training should stop early."""
        if val_accuracy > self.best_val_accuracy + self.config.EARLY_STOPPING_MIN_DELTA: 
            self.epochs_without_improvement = 0
            return False
        else:
            self.epochs_without_improvement += 1
            if self.epochs_without_improvement >= self.config.EARLY_STOPPING_PATIENCE:
                return True
        return False
    
    def train(self):
        """Full training loop."""
        print(f"\n{'='*80}")
        print(f"Starting training on {self. device}")
        print(f"{'='*80}\n")
        
        for epoch in range(self.config.NUM_EPOCHS):
            print(f"\n{'─'*80}")
            print(f"EPOCH {epoch + 1}/{self.config.NUM_EPOCHS}")
            print(f"{'─'*80}")
            
            # Train
            train_loss = self.train_epoch(epoch)
            
            # Validate
            val_loss, val_accuracy = self. validate()
            
            # Print epoch summary
            print(f"\n{'─'*80}")
            print(f"Epoch {epoch + 1} Summary:")
            print(f"  Train Loss:     {train_loss:.4f}")
            print(f"  Val Loss:      {val_loss:.4f}")
            print(f"  Val Accuracy:  {val_accuracy:.4f} ({val_accuracy*100:.2f}%)")
            print(f"  Learning Rate: {self.optimizer.param_groups[0]['lr']:.2e}")
            
            # Check if best model
            is_best = val_accuracy > self.best_val_accuracy
            if is_best:
                self.best_val_accuracy = val_accuracy
                self.best_val_loss = val_loss
                print(f"  🎉 New best model!  (Accuracy: {val_accuracy:.4f})")
            
            print(f"{'─'*80}\n")
            
            # Save checkpoint
            self.save_checkpoint(epoch, val_loss, val_accuracy, is_best)
            
            # Save training history
            self.save_history()
            
            # Early stopping check
            if self.check_early_stopping(val_accuracy):
                print(f"\n⚠️  Early stopping triggered!")
                print(f"   No improvement for {self.config. EARLY_STOPPING_PATIENCE} epochs")
                break
        
        print(f"\n{'='*80}")
        print(f"Training completed!")
        print(f"  Best Val Accuracy: {self.best_val_accuracy:.4f} ({self.best_val_accuracy*100:.2f}%)")
        print(f"  Best Val Loss:     {self.best_val_loss:.4f}")
        print(f"{'='*80}\n")
    
    def save_checkpoint(self, epoch, val_loss, val_accuracy, is_best=False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch + 1,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self. optimizer.state_dict() if self.config.SAVE_OPTIMIZER_STATE else None,
            'val_loss': val_loss,
            'val_accuracy': val_accuracy,
            'best_val_accuracy': self.best_val_accuracy,
            'history': self.history,
            'config': {
                'num_labels': self.config.NUM_LABELS,
                'dropout_rate': self.config. DROPOUT_RATE,
                'learning_rate': self.config.LEARNING_RATE,
                'model_name': self.config.MODEL_NAME
            }
        }
        
        # Save best model
        if is_best: 
            best_path = self.config. CHECKPOINT_DIR / self.config. BEST_MODEL_FILENAME
            torch.save(checkpoint, best_path)
            print(f"  💾 Saved best model to:  {best_path}")
        
        # Save latest model
        latest_path = self.config.CHECKPOINT_DIR / self.config.LATEST_MODEL_FILENAME
        torch.save(checkpoint, latest_path)
    
    def save_history(self):
        """Save training history to JSON."""
        history_path = self. config.CHECKPOINT_DIR / self.config.HISTORY_FILENAME
        with open(history_path, 'w') as f:
            json.dump(self. history, f, indent=2)


def main():
    """Main training script."""
    
    # Print configuration
    Config.print_config()
    
    # Set random seed for reproducibility
    Config.set_seed()
    
    # ========== Load Datasets ==========
    print("Loading datasets...")
    try:
        train_dataset, val_dataset, tokenizer = load_csv_datasets(
            train_csv_path=str(Config.TRAIN_CSV),
            val_csv_path=str(Config.VAL_CSV),
            max_length=Config.MAX_LENGTH,
            text_column=Config.TEXT_COLUMN,
            label_column=Config.LABEL_COLUMN
        )
        print(f"✓ Datasets loaded successfully")
        print(f"  Training samples:    {len(train_dataset)}")
        print(f"  Validation samples: {len(val_dataset)}\n")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print(f"\nExpected file locations:")
        print(f"  Train CSV:  {Config.TRAIN_CSV}")
        print(f"  Val CSV:   {Config.VAL_CSV}")
        return
    
    # ========== Create DataLoaders ==========
    print("Creating data loaders...")
    train_loader = DataLoader(
        train_dataset, 
        batch_size=Config.BATCH_SIZE, 
        shuffle=True,
        num_workers=Config. NUM_WORKERS,
        pin_memory=Config.PIN_MEMORY
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=Config.EVAL_BATCH_SIZE, 
        shuffle=False,
        num_workers=Config.NUM_WORKERS,
        pin_memory=Config.PIN_MEMORY
    )
    print(f"✓ Data loaders created")
    print(f"  Train batches: {len(train_loader)}")
    print(f"  Val batches:   {len(val_loader)}\n")
    
    # ========== Initialize Model ==========
    print("Initializing model...")
    model = CustomDistilBertForSequenceClassification(
        num_labels=Config.NUM_LABELS,
        dropout_rate=Config.DROPOUT_RATE
    )
    model.to(Config.DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p. numel() for p in model.parameters() if p.requires_grad)
    print(f"✓ Model initialized")
    print(f"  Total parameters:      {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}\n")
    
    # ========== Setup Optimizer ==========
    optimizer = AdamW(
        model.parameters(), 
        lr=Config. LEARNING_RATE,
        weight_decay=Config.WEIGHT_DECAY,
        eps=Config.ADAM_EPSILON
    )
    print(f"✓ Optimizer:  AdamW (lr={Config.LEARNING_RATE:.2e}, wd={Config.WEIGHT_DECAY})\n")
    
    # ========== Create Trainer and Train ==========
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        device=Config.DEVICE,
        config=Config
    )
    
    # Start training
    trainer.train()
    
    print(f"✓ Checkpoints saved to:  {Config.CHECKPOINT_DIR}")
    print(f"  - {Config.BEST_MODEL_FILENAME} (best validation accuracy)")
    print(f"  - {Config.LATEST_MODEL_FILENAME} (most recent epoch)")
    print(f"  - {Config.HISTORY_FILENAME} (loss/accuracy curves)")


if __name__ == "__main__":
    main()