import torch
from torch import nn


class FugueModel(nn.Module):

    def __init__(self, vocabulary_size: int, pad_id: int, embedding_size: int = 128, context_length: int = 256, number_of_heads: int = 4, number_of_layers: int = 3, dropout: float = 0.1):
        super().__init__()

        self.context_length = context_length
        self.pad_id = pad_id
        self.token_embedding = nn.Embedding(
            vocabulary_size,
            embedding_size,
            padding_idx=pad_id            
            )
        self.position_embedding = nn.Embedding(
            context_length,
            embedding_size            
            )

        self.blocks = nn.ModuleList(
            [
                nn.TransformerEncoderLayer(
                    d_model=embedding_size,
                    nhead=number_of_heads,
                    dim_feedforward=4 * embedding_size,
                    dropout=dropout,
                    activation="gelu",
                    batch_first=True,
                    norm_first=True                   
                    )
                for _ in range(number_of_layers)
                ]
            )
        self.final_norm = nn.LayerNorm(embedding_size)
        self.output_layer = nn.Linear(
            embedding_size,
            vocabulary_size
            )


    def forward(self, input_ids: torch.Tensor, padding_mask: torch.Tensor | None=None) -> torch.Tensor:

        sequence_length = input_ids.shape[1]

        if sequence_length > self.context_length:
            raise ValueError("Input length must be smaller than or equal to context length")

        if padding_mask is None:
            padding_mask = input_ids == self.pad_id

        positions = torch.arange(
            sequence_length,
            device=input_ids.device
            )

        x = self.token_embedding(input_ids) + self.position_embedding(positions)

        causal_mask = torch.ones(
            sequence_length,
            sequence_length,
            dtype=torch.bool,
            device=input_ids.device,
            ).triu(diagonal=1)

        for block in self.blocks:
            x=block(x, src_mask = causal_mask, src_key_padding_mask= padding_mask)

        x = self.final_norm(x)
        return self.output_layer(x)