from pathlib import Path

from fugue.constraints import allowed_next_tokens

import torch

from fugue.model import FugueModel
from fugue.tokenize import tokens_to_ids, ids_to_tokens

def load_model(path:Path, device: torch.device) -> tuple[FugueModel, dict[str,int]]:
    checkpoint= torch.load(
        path,
        map_location="cpu",
        weights_only=True
        )

    model = FugueModel(**checkpoint["model_config"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    return model, checkpoint["vocabulary"]


@torch.inference_mode()
def generate(
    model: FugueModel,
    vocabulary: dict[str,int],
    prompt: list[str],
    max_new_tokens: int = 1000,
    temperature: float = 1.0    
    ) -> list[str]:

    model.eval()
    device = next(model.parameters()).device

    generated_ids = tokens_to_ids(prompt,vocabulary)
    end_id = vocabulary["SCORE_END"]

    if generated_ids[-1] == end_id:
        return ids_to_tokens(generated_ids,vocabulary)

    for _ in range(max_new_tokens):
        context = generated_ids[-model.context_length:]

        input_ids = torch.tensor(
            [context],
            dtype=torch.long,
            device=device
            )

        logits = model(input_ids)

        next_logits = logits[0, -1, :].clone()

        generated_tokens = ids_to_tokens(generated_ids, vocabulary)

        allowed_ids = tokens_to_ids(allowed_next_tokens(generated_tokens,vocabulary), vocabulary)
      
        if not allowed_ids:
            raise ValueError("No valid next token")

        masked_logits = torch.full_like(next_logits, float("-inf"))
        masked_logits[allowed_ids] = next_logits[allowed_ids]

        probabilities = torch.softmax(
            masked_logits / temperature,
            dim=-1
            )

        next_id = torch.multinomial(
            probabilities,
            num_samples=1
            ).item()

        generated_ids.append(next_id)

        if next_id == end_id:
            break

    return ids_to_tokens(generated_ids, vocabulary)



def main():
    device = torch.device("cuda")

    model, vocabulary = load_model(Path("checkpoints/epoch_010.pt"),device)

    prompt = [
        "SCORE_START",
        "KEY_C(0)_MAJOR",
        "VOICE_COUNT_3",
        "BAR_START",
        "TS_4_4"
        ]

    tokens = generate(
        model,
        vocabulary,
        prompt,
        max_new_tokens=1000,
        temperature=0.8
        )
    print(" ".join(tokens))

    if tokens[-1] != "SCORE_END":
        print("\nToken limit reached before SCORE_END")

if __name__ == "__main__":
    main()

