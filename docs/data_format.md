# Score data format

**Version:** `1.0`  
**Location:** `docs/data_format.md`

Store one JSON file per score in `data/processed/<corpus>/`. Keep the original
`.krn` files unchanged in `data/raw/`. Processed scores keep their original key;
transposition and model tokens are separate outputs.

## 1. Timing

**One quarter note equals `"1"`.** All fields ending in `_q` use this unit,
regardless of meter or tempo.

| Duration | Value |
| --- | --- |
| Whole note | `"4"` |
| Half note | `"2"` |
| Quarter note | `"1"` |
| Eighth note | `"1/2"` |
| Sixteenth note | `"1/4"` |
| Dotted quarter note | `"3/2"` |
| Eighth-note triplet | `"1/3"` |

Store times as strings with reduced fractions. Use Python's `Fraction` for
calculations, not floats. Write `"1/2"`, not `"0.5"` or `"2/4"`; write whole
values as `"1"`, not `"1/1"`.

- `onset_q`: time from the start of the score, beginning at `"0"`.
- `duration_q`: length of the note, rest or measure.
- End time: `onset_q + duration_q`.

Events with the same onset happen together. An event starting when another ends
does not overlap it. Onsets cannot be negative; durations must be positive.

## 2. Score fields

Use `null` where allowed when a value is unknown. 

| Field | Contents |
| --- | --- |
| `schema_version` | `"1.0"`. |
| `piece_id` | ID for this score. |
| `metadata` | Title, composer, key, voice count and total duration. |
| `provenance` | Source and processing details. |
| `voices` | Voice definitions. |
| `measures` | Measure boundaries and time signatures. |
| `events` | Notes and rests. |

IDs are nonempty strings, except the numeric voice and measure IDs below.

### Metadata

- `title`, `composer`: strings or `null`.
- `voice_count`: positive integer matching the number of voices.
- `duration_q`: total score length, including rests.
- `key`: `null`, or an object with `tonic_step` (A-G), `tonic_alter` (integer
  semitone alteration), `mode` (`major`, `minor`, `other`)

### Provenance

- `source_id`: link to the source manifest.
- `source_format`: `humdrum`, `musicxml` or `synthetic`.
- `source_path`: project-relative path using `/` separators.

Keep source URLs, repository revisions and license details in the manifest.

## 3. Voices and measures

Each voice has an integer `id`, numbered consecutively from 1. A voice keeps its ID when it crosses another voice or changes
staff. Each voice contains one musical line, with rests before its first entry and wherever it is silent.

Each measure contains:

| Field | Meaning |
| --- | --- |
| `index` | Consecutive integer starting at 0. |
| `onset_q`, `duration_q` | Absolute start and actual length. |
| `time_signature` | Positive integer `numerator` and `denominator`. |
| `kind` | `regular`, `pickup` or `irregular`. |

A regular measure lasts `numerator * 4 / denominator` quarter notes. Both 3/4
and 6/8 therefore last `"3"`. Include the effective time signature in every
measure.

A one-quarter pickup starts at `"0"` and lasts `"1"`; the next measure starts at
`"1"`. 

## 4. Notes and rests

Each event has these fields:

| Field | Meaning |
| --- | --- |
| `id` | Unique string within the score. |
| `type` | `note` or `rest`. |
| `voice` | Existing voice ID. |
| `measure_index` | Existing measure index. |
| `onset_q`, `duration_q` | Absolute start and segment length. |
| `pitch` | Pitch object for a note; `null` for a rest. |
| `tie` | `start`, `continue`, `stop` or `null`. |

Example event: voice 2 plays E-flat 4 for one eighth-note triplet at the start
of the score.

```json
{
  "id": "e0001",
  "type": "note",
  "voice": 2,
  "measure_index": 0,
  "onset_q": "0",
  "duration_q": "1/3",
  "pitch": {"step": "E", "alter": -1, "octave": 4},
  "tie": null
}
```

Pitch uses a letter A-G, an integer alteration (`-1` flat, `0` natural, `1` sharp)
and an integer octave. Double accidentals use `-2` or `2`. Middle C is C4.
Preserve spelling: E-flat and D-sharp remain different records.

A rest has `pitch: null` and `tie: null`. 

Keep tied segments separate. A chain is `start`, zero or more `continue`
segments, then `stop`. Segments must touch in time and have the same voice and
spelled pitch. An untied note uses `null`.

Split notes or rests at barlines so every event fits inside one measure. Add ties
for split notes, leave rests untied.

## 5. Saving and later processing

Write UTF-8 JSON with two-space indentation and a final newline. Sort voices by
ID, measures by index, and events by numeric `(onset_q, voice, id)`.

Keep normalized scores and tokens in `data/derived/`. Normalize an entire piece
by one spelled interval and record how to reverse it. 
