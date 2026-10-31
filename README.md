# fugue-generator
A Python project exploring Transformer-based generation of polyphonic music, using fugues from Bach’s Well-Tempered Clavier.

The project covers the full workflow: registering Humdrum sources, parsing scores into a structured representation, tokenizing music, training an autoregressive model, generating constrained continuations, and exporting to MusicXML for notation and playback in MuseScore.

## Current status

A working research prototype. Generated scores can be exported and listened to in MuseScore. 

## Features

- Structured score representation with notes, rests, voices, measures, keys, and ties.
- Humdrum (`.krn`) parsing through music21.
- Reversible musical token encoding and integer-ID vocabulary.
- A causal Transformer with learned token and position embeddings.
- Checkpoint saving, validation-based model selection, and held-out evaluation.
- Constrained sampling for token order, voice timing, bar completion, and ties.
- MusicXML export with one staff per voice.
- Comparison of original-key training with key-normalised training.

## Model and training

The model uses learned token and position embeddings, causally masked Transformer blocks, layer normalisation, and a linear output layer producing logits over the vocabulary. 
Training windows contain a sequence of input tokens and the same sequence shifted by one token as targets. A causal attention mask prevents the model from seeing future tokens.
Validation loss is used for checkpoint selection and early stopping.

## Evaluation: key normalisation

Two representations were compared:
- Original keys: fugues retained their original pitches and keys.
- Normalised keys: major fugues were transposed to C major and minor fugues to A minor.
Both were evaluated on the same four held-out compositions.

| Training representation | Test cross-entropy | Test perplexity |
| --- | ---: | ---: |
| Original keys | 0.9433 | 2.5684 |
| C major / A minor | 0.8636 | 2.3716 |

## Constrained generation

The model proposes next-token scores, and the decoder masks invalid choices before sampling. The current constraints enforce:
- Header and event-token grammar.
- Nondecreasing event positions within each bar.
- Continuous coverage of each voice.
- Durations that fit within the bar.
- One note at a time per voice.
- Matching pitches for tied notes.
- Bar closure only after every voice fills the bar.
- Score completion only when no ties remain open.

## Main modules

| Module | Responsibility |
| --- | --- |
| `schema.py` | Score dataclasses, validation, and JSON serialization |
| `ingest.py` | Source registration, checksums, and manifest access |
| `parse.py` | Humdrum-to-score conversion |
| `transpose.py` | Key normalization before tokenization |
| `tokenize.py` | Score/token conversion and vocabulary utilities |
| `dataset.py` | Training windows, shifted targets, and padding |
| `model.py` | Transformer architecture |
| `train.py` | Training, validation, and checkpoint selection |
| `evaluate.py` | Held-out predictive evaluation |
| `constraints.py` | Valid next-token selection |
| `generate.py` | Checkpoint loading and constrained sampling |
| `export.py` | music21 conversion and MusicXML export |

## Planned work
- Improve support for pickups, irregular bars, and chords.
- Build an interface for a subject editor with playback and generation controls.
- Explore explicit subject conditioning and longer-range musical structure.

