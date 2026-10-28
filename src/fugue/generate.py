from pathlib import Path

from fugue.constraints import allowed_next_tokens
from fugue.export import export_musicxml
from fugue.parse import parse_humdrum_kern

import torch

from fugue.model import FugueModel
from fugue.tokenize import score_to_tokens, tokens_to_ids, ids_to_tokens, tokens_to_score

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
    max_new_tokens: int = 10000,
    max_bars: int = 24,
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

        allowed_tokens = allowed_next_tokens(generated_tokens,vocabulary)

        current_bar = generated_tokens.count("BAR_START")

        if current_bar >= max_bars:
            allowed_tokens = [
                token for token in allowed_tokens 
                if token not in {"TIE_START", "TIE_CONTINUE"}
                ]

        if (generated_tokens[-1]=="BAR_END" and current_bar >= max_bars):
            if "SCORE_END" not in allowed_tokens:
                raise ValueError("Reached final bar with unresolved ties")

            allowed_tokens = ["SCORE_END"]
           

        allowed_ids = tokens_to_ids(allowed_tokens, vocabulary)
      
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

def find_bar_end_index(tokens: list[str], n: int) -> int:
    if n < 1:
        raise ValueError("n must be at least 1")

    bar_count = 0

    for index, token in enumerate(tokens):
        if token == "BAR_END":
            bar_count += 1

            if bar_count == n:
                return index

    raise ValueError(f"Only {bar_count} complete bars found; requested {n}")

def main():
    device = torch.device("cuda")

    model, vocabulary = load_model(Path("checkpoints/epoch_010.pt"),device)

    
    
    score = parse_humdrum_kern("src-99688eb7307449b888140d3c8fb73148")
    input_score_tokens=score_to_tokens(score)

    prompt_end=find_bar_end_index(input_score_tokens, 3)

    prompt = input_score_tokens[0:prompt_end]

    tokens = generate(
        model,
        vocabulary,
        prompt,
        max_new_tokens=100000,
        temperature=0.8
        )

    if tokens[-1] != "SCORE_END":
        raise ValueError("\nToken limit reached before SCORE_END")


    score = tokens_to_score(tokens)
    export_musicxml(score, Path("outputs/generated.musicxml"))

if __name__ == "__main__":
    main()

