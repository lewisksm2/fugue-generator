import torch
from torch.utils.data import Dataset
from pathlib import Path
import json


class FugueDataset(Dataset):
    def __init__(
        self,
        scores_dir: Path,
        context_length: int,
        pad_id: int        
        ):

        if context_length<1:
            raise ValueError("context length must be positive")

        self.context_length = context_length
        self.pad_id = pad_id
        self.examples = []

        for path in scores_dir.iterdir():
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"Creating examples for {data['source_id']}")
            token_ids = data["token_ids"]

            for start in range(0,len(token_ids)-1,context_length):

                window = token_ids[start:start+context_length+1]

                self.examples.append((data["source_id"],window))

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> dict:
        source_id, window = self.examples[index]

        inputs = window[:-1]
        targets = window[1:]

        real_length = len(inputs)
        padding_length = self.context_length - real_length

        inputs = inputs + [self.pad_id]*padding_length
        targets = targets + [-100]*padding_length

        return {
            "input_ids": torch.tensor(inputs, dtype=torch.long),
            "targets": torch.tensor(targets, dtype=torch.long),
            "padding_mask": torch.tensor(
                [False] * real_length + [True] * padding_length,
                dtype=torch.bool
                ),
            "source_id": source_id            
            }

