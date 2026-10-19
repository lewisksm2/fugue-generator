import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Literal

SCHEMA_VERSION = "1.0"

PitchStep = Literal["A","B","C","D","E","F","G"]
PitchAlter = Literal[-2,-1,0,1,2]


@dataclass
class Pitch:
    step: PitchStep
    alter: PitchAlter
    octave: int

    def __post_init__(self) -> None:
        if self.step not in ("A","B","C","D","E","F","G"):
            raise ValueError("Pitch step must be A-G")
        if type(self.alter) is not int:
            raise ValueError("Pitch alter must be an integer")
        if self.alter not in (-2,-1,0,1,2):
            raise ValueError("Pitch alter must be >=-2 and <=2")
        if type(self.octave) is not int:
            raise ValueError("Pitch octave must be an integer")   


@dataclass
class Event:
    id: str
    type: Literal["note", "rest"]
    voice: int
    measure_index: int
    onset_q: Fraction
    duration_q: Fraction
    pitch: Pitch | None
    tie: Literal["start", "continue", "stop"] | None

    def __post_init__(self) -> None:
        if not isinstance(self.id,str) or not self.id.strip():
            raise ValueError("Event id must be a nonempty string")
        if self.type not in ("note", "rest"):
            raise ValueError("Event type must be note or rest")
        if self.type == "note" and not isinstance(self.pitch, Pitch):
            raise ValueError("A note must have a pitch")
        if self.type == "rest" and (self.pitch is not None or self.tie is not None):
            raise ValueError("A rest must have pitch=None and tie=None")
        if type(self.voice) is not int:
            raise ValueError("Event voice must be an integer")
        if self.voice < 1:
            raise ValueError("Event voice must be positive")
        if type(self.measure_index) is not int:
            raise ValueError("Event measure_index must be an integer")
        if self.measure_index < 0:
            raise ValueError("Event measure_index must be nonnegative")
        if not isinstance(self.onset_q, Fraction):
            raise ValueError("Event onset_q must be a fraction")
        if self.onset_q < 0:
            raise ValueError("Event onset_q must be nonnegative")
        if not isinstance(self.duration_q, Fraction):
            raise ValueError("Event duration_q must be a fraction")
        if self.duration_q <= 0:
            raise ValueError("Event duration_q must be positive")
        if self.tie not in ("start", "continue", "stop", None):
            raise ValueError("Invalid tie value")


@dataclass
class TimeSignature:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if type(self.numerator) is not int:
            raise ValueError("TimeSignature numerator must be an integer")
        if self.numerator <= 0:
            raise ValueError("TimeSignature numerator must be positive")
        if type(self.denominator) is not int:
            raise ValueError("TimeSignature denominator must be an integer")
        if self.denominator <= 0:
            raise ValueError("TimeSignature denominator must be positive")


@dataclass
class Measure:
    index: int
    onset_q: Fraction
    duration_q: Fraction
    time_signature: TimeSignature
    kind: Literal["regular", "pickup", "irregular"]

    def __post_init__(self) -> None:
        if type(self.index) is not int:
            raise ValueError("Measure index must be an integer")
        if self.index < 0:
            raise ValueError("Measure index must be nonnegative")
        if not isinstance(self.onset_q, Fraction):
            raise ValueError("Measure onset_q must be a Fraction")
        if self.onset_q < 0:
            raise ValueError("Measure onset_q must be nonnegative")
        if not isinstance(self.duration_q, Fraction):
            raise ValueError("Measure duration_q must be a Fraction")
        if self.duration_q <= 0:
            raise ValueError("Measure duration_q must be positive")
        if not isinstance(self.time_signature, TimeSignature):
            raise ValueError("Measure time_signature must be a TimeSignature")
        if self.kind not in ("regular", "pickup", "irregular"):
            raise ValueError("Invalid measure kind")


@dataclass
class Key:
    tonic_step: PitchStep
    tonic_alter: PitchAlter
    mode: Literal["major", "minor", "other"]

    def __post_init__(self) -> None:
        if self.tonic_step not in ("A","B","C","D","E","F","G"):
            raise ValueError("Key tonic_step must be A-G")
        if type(self.tonic_alter) is not int:
            raise ValueError("Key tonic_alter must be an integer")
        if self.tonic_alter not in (-2,-1,0,1,2):
            raise ValueError("Key tonic_alter must be <=2 and >=-2")
        if self.mode not in ("major", "minor", "other"):
            raise ValueError("Invalid key mode")


@dataclass
class Metadata:
    title: str | None
    composer: str | None
    voice_count: int
    duration_q: Fraction
    key: Key | None

    def __post_init__(self) -> None:
        if self.title is not None and not isinstance(self.title,str):
            raise ValueError("title must be a string or None")
        if self.composer is not None and not isinstance(self.composer,str):
            raise ValueError("composer must be a string or None")
        if type(self.voice_count) is not int:
            raise ValueError("voice_count must be an integer")
        if self.voice_count < 1:
            raise ValueError("voice_count must be positive")
        if not isinstance(self.duration_q, Fraction):
            raise ValueError("duration_q must be a Fraction")
        if self.duration_q <= 0:
            raise ValueError("duration_q must be positive")
        if self.key is not None and not isinstance(self.key, Key):
            raise ValueError("key must be a Key or None")


@dataclass
class Provenance:
    source_id: str
    source_format: Literal["humdrum", "musicxml", "synthetic"]
    source_path: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id,str) or not self.source_id.strip():
            raise ValueError("source_id must be a nonempty string")
        if self.source_format not in ("humdrum", "musicxml", "synthetic"):
            raise ValueError("Invalid source format")
        if self.source_path is None:
            if self.source_format != "synthetic":
                raise ValueError("Imported scores need a source_path")

        else:
            if not isinstance(self.source_path, str):
                raise ValueError("source_path must be a string")


@dataclass
class Voice:
    id: int

    def __post_init__(self) -> None:
        if type(self.id) is not int:
            raise ValueError("Voice id must be an integer")
        if self.id < 1:
            raise ValueError("Voice id must be positive")


@dataclass
class KeyChange:
    onset_q: Fraction
    sharps: int

    def __post_init__(self) -> None:
        if not isinstance(self.onset_q, Fraction):
            raise ValueError("onset_q must be a Fraction")
        if self.onset_q < 0:
            raise ValueError("onset_q must be nonnegative")
        if type(self.sharps) is not int:
            raise ValueError("sharps must be an integer")


@dataclass
class Score:
    schema_version: str
    piece_id: str
    metadata: Metadata
    provenance: Provenance
    voices: list[Voice]
    measures: list[Measure]
    events: list[Event]
    key_signatures: list[KeyChange]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version: {self.schema_version}")
        if not isinstance(self.piece_id, str) or not self.piece_id.strip():
            raise ValueError("piece_id must be a nonempty string")
        if not isinstance(self.metadata, Metadata):
            raise ValueError("Score needs metadata")
        if not isinstance(self.provenance, Provenance):
            raise ValueError("Score needs provenance")
        for name, item_type in (("voices", Voice), ("measures", Measure), ("events", Event)):
            items = getattr(self, name)
            if (
                not isinstance(items,list)
                or not items
                or not all(isinstance(x,item_type) for x in items)
                ):
                raise ValueError(f"{name} must be a nonempty list of {item_type.__name__} objects")
        voice_ids = [voice.id for voice in self.voices]
        if voice_ids != list(range(1,self.metadata.voice_count+1)):
            raise ValueError("Voice IDs must range from 1 to voice_count")
        if [m.index for m in self.measures] != list(range(len(self.measures))):
            raise ValueError("Measure indices must run from 0 without gaps")
        if len({event.id for event in self.events}) != len(self.events):
            raise ValueError("Event IDs must be unique")
        for event in self.events:
            if event.voice not in voice_ids:
                raise ValueError(f"Unknown voice in event {event.id}")
            if event.measure_index >= len(self.measures):
                raise ValueError(f"Unknown measure in event {event.id}")

        if not isinstance(self.key_signatures, list) or not all(isinstance(item, KeyChange) for item in self.key_signatures):
            raise ValueError("key_signatures must be a list of KeyChange objects")


def _json_default(value: object) -> str:
    if isinstance(value,Fraction):
        return(str(value))
    raise TypeError(f"Cannot serialize {type(value).__name__} to JSON")

def _read_time(value: str) -> Fraction:
    if not isinstance(value, str):
        raise ValueError("JSON times must be strings")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Invalid time: {value}") from exc
    if str(result) != value:
        raise ValueError(f"Use {str(result)} instead of {value}")
    return result


def score_to_json(score: Score) -> str:
    data = json.loads(json.dumps(asdict(score), default=_json_default))
    data["voices"].sort(key=lambda voice: voice["id"])
    data["measures"].sort(key=lambda measure: measure["index"])
    data["events"].sort(key=lambda event: (Fraction(event["onset_q"]), event["voice"], event["id"]))
    data["key_signatures"].sort(key=lambda key_change: Fraction(key_change["onset_q"]))
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def score_from_json(text: str) -> Score:
    data = json.loads(text)

    metadata = dict(data["metadata"])
    metadata["duration_q"] = _read_time(metadata["duration_q"])
    if metadata["key"] is not None:
        metadata["key"] = Key(**metadata["key"])

    measures = []
    for raw in data["measures"]:
        item = dict(raw)
        item["onset_q"] = _read_time(item["onset_q"])
        item["duration_q"] = _read_time(item["duration_q"])
        item["time_signature"] = TimeSignature(**item["time_signature"])
        measures.append(Measure(**item))

    events = []
    for raw in data["events"]:
        item = dict(raw)
        item["onset_q"] = _read_time(item["onset_q"])
        item["duration_q"] = _read_time(item["duration_q"])
        if item["pitch"] is not None:
            item["pitch"] = Pitch(**item["pitch"])
        events.append(Event(**item))

    key_signatures = []
    for raw in data["key_signatures"]:
        item = dict(raw)
        item["onset_q"] = _read_time(item["onset_q"])
        key_signatures.append(KeyChange(**item))

    fields = dict(data)
    fields.update(
        metadata=Metadata(**metadata),
        provenance=Provenance(**data["provenance"]),
        voices=[Voice(**voice) for voice in data["voices"]],
        measures=measures,
        events=events,
        key_signatures=key_signatures
        )
    return Score(**fields)