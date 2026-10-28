import torch
from torch import nn
from torch.utils.data import DataLoader
from pathlib import Path
from fugue.model import FugueModel
from fugue.dataset import FugueDataset
from fugue.tokenize import load_vocabulary

def train_one_epoch(model, loader, optimizer, loss_function, device):
    model.train()

    total_loss=0.0
    total_targets=0

    for batch in loader:
        inputs = batch["input_ids"].to(device)
        targets = batch["targets"].to(device)
        padding_mask = batch["padding_mask"].to(device)

        optimizer.zero_grad()

        logits = model(inputs, padding_mask)
        vocabulary_size = logits.shape[-1]

        loss = loss_function(
            logits.reshape(-1,vocabulary_size),
            targets.reshape(-1)
            )
        loss.backward()
        optimizer.step()

        target_count = (targets != -100).sum().item()
        total_loss += loss.item()*target_count
        total_targets += target_count

    return total_loss / total_targets


@torch.inference_mode()
def evaluate(model, loader, loss_function, device):
    model.eval()

    total_loss=0.0
    total_targets=0

    for batch in loader:
        inputs = batch["input_ids"].to(device)
        targets = batch["targets"].to(device)
        padding_mask = batch["padding_mask"].to(device)

        logits = model(inputs, padding_mask)
        vocabulary_size = logits.shape[-1]

        loss = loss_function(
            logits.reshape(-1,vocabulary_size),
            targets.reshape(-1)
            )
        
        target_count = (targets != -100).sum().item()
        total_loss += loss.item()*target_count
        total_targets += target_count

    return total_loss / total_targets
    



def save_checkpoint(
    path: Path,
    model,
    optimizer,
    completed_epochs: int,
    loss: float,
    model_config: dict,
    vocabulary: dict[str, int]    
    ) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "completed_epochs": completed_epochs,
            "loss": loss,
            "model_config": model_config,
            "vocabulary": vocabulary
            },
            path
        )

def main():
   
    vocabulary = load_vocabulary()

    train_dataset = FugueDataset(
        scores_dir = Path("data/derived/tokens_v1/scores/train"),
        context_length=256,
        pad_id = vocabulary["PAD"]
        )

    validation_dataset = FugueDataset(
        scores_dir = Path("data/derived/tokens_v1/scores/validation"),
        context_length=256,
        pad_id = vocabulary["PAD"]
        )

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

    validation_loader = DataLoader(validation_dataset, batch_size=8, shuffle=True)

    device=torch.device("cuda")
    print(f"Training on: {device}")

    model_config = {
        "vocabulary_size": len(vocabulary),
        "pad_id": vocabulary["PAD"],
        "embedding_size": 128,
        "context_length": 256,
        "number_of_heads": 4,
        "number_of_layers": 3,
        "dropout": 0.4
        }

    model = FugueModel(**model_config).to(device)

    loss_function = nn.CrossEntropyLoss(ignore_index=-100)

    optimizer= torch.optim.AdamW(model.parameters(), lr=0.001)

    best_validation_loss = float("inf")
    epochs_without_improvement = 0
    patience = 10

    for epoch in range(100):
        training_loss = train_one_epoch(
            model,
            train_loader,
            optimizer,
            loss_function,
            device
            )
        validation_loss = evaluate(
            model,
            validation_loader,
            loss_function,
            device
            )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            epochs_without_improvement = 0
            
            save_checkpoint(
                path=Path(f"checkpoints/epoch_{epoch + 1:03d}.pt"),
                model=model,
                optimizer=optimizer,
                completed_epochs=epoch + 1,
                loss=training_loss,
                model_config=model_config,
                vocabulary=vocabulary        
                )
        else:
            epochs_without_improvement +=1

        print(
            f"Epoch {epoch+1}:"
            f"training loss={training_loss:.4f}, "
            f"validation loss={validation_loss:.4f}"
            )

        if epochs_without_improvement > patience:
            print("Early stopping")
            break

if __name__ == "__main__":
    main()