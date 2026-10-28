from fugue.train import evaluate
from fugue.generate import load_model
from fugue.dataset import FugueDataset

import math
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader

def main():
    device = torch.device("cuda")

    model, vocabulary = load_model(Path("checkpoints/best.pt"), device)

    test_dataset = FugueDataset(
        scores_dir = Path("data/derived/tokens_v1/scores/test"),
        context_length = 256,
        pad_id = vocabulary["PAD"]
       )

    test_loader = DataLoader(
        test_dataset,
        batch_size=8,
        shuffle=False
        )

    loss_function = nn.CrossEntropyLoss(ignore_index=-100)

    test_loss = evaluate(
        model,
        test_loader,
        loss_function,
        device
        )

    perplexity = math.exp(test_loss)

    print(f"Test cross-entropy: {test_loss:.4f}")
    print(f"Test perplexity: {perplexity:.4f}")


if __name__ == "__main__":
    main()