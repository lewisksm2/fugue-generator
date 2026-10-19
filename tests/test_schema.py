from fractions import Fraction

import pytest

from fugue.schema import(
    Event,
    KeyChange,
    Measure,
    Metadata,
    Pitch,
    Provenance,
    Score,
    TimeSignature,
    Voice,
    score_from_json,
    score_to_json
    )

@pytest.fixture
def example_score() -> Score:
    """One measure containing two voices. Voice 1 plays a triplet and Voice 2 plays a rest."""
    return Score(
        schema_version="1.0",
        piece_id="test_piece",
        metadata=Metadata(
            title=None,
            composer=None,
            voice_count=2,
            duration_q=Fraction(4),
            key=None       
            ),
        provenance=Provenance(
            source_id="test_source",
            source_format="synthetic",
            source_path=None
            ),
        voices=[Voice(id=1), Voice(id=2)],
        measures=[
            Measure(
                index=0,
                onset_q=Fraction(0),
                duration_q=Fraction(4),
                time_signature=TimeSignature(4,4),
                kind="regular"
                )
            ],
        events=[
            Event(
                id="e1",
                type="note",
                voice=1,
                measure_index=0,
                onset_q=Fraction(0),
                duration_q=Fraction(1,3),
                pitch=Pitch("C",0,4),
                tie=None
                ),
            Event(
                id="e2",
                type="rest",
                voice=2,
                measure_index=0,
                onset_q=Fraction(0),
                duration_q=Fraction(4),
                pitch=None,
                tie=None
                )
            ],
        key_signatures=[]       
        )


def test_json_round_trip(example_score):
    text = score_to_json(example_score)
    restored = score_from_json(text)

    assert restored == example_score
    assert restored.events[0].duration_q == Fraction(1,3)

def test_initial_key_signature_round_trip(example_score):
    example_score.key_signatures = [
        KeyChange(Fraction(0),-2)
        ]

    text = score_to_json(example_score)
    restored = score_from_json(text)

    assert restored == example_score


@pytest.mark.parametrize("alter", [True, 1.0, -3, 3])
def test_invalid_pitch_alteration(alter):
    with pytest.raises(ValueError):
        Pitch(step="C", alter=alter, octave=4)


@pytest.mark.parametrize("numerator, denominator", [(0, 4), (4, 0)])
def test_invalid_time_signature(numerator, denominator):
    with pytest.raises(ValueError):
        TimeSignature(numerator, denominator)