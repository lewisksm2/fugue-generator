from pathlib import Path
import music21
from fractions import Fraction
from fugue.schema import(
    Event,
    KeyChange,
    Key,
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
from fugue.ingest import(
    manifest_lookup
    )

def parse_key(path: Path) -> Key:
    score = music21.converter.parse(path)
    key_signature=score.flatten().getElementsByClass(music21.key.Key)[0]
    tonic = key_signature.tonic.name
    tonic_step = "".join(filter(str.isalpha, tonic))
    str_alter = "".join(filter(lambda c: not c.isalpha(),tonic))
    if str_alter=="":
        tonic_alter=0
    elif str_alter=="#":
        tonic_alter=1
    elif str_alter=="-":
        tonic_alter=-1
    else:
        raise ValueError("Error reading key signature from .krn file")
    mode = key_signature.mode
    return Key(
        tonic_step = tonic_step,
        tonic_alter = tonic_alter,
        mode = mode        
        )

def parse_humdrum_kern(source_id: str) -> Score:
    manifest_entry = manifest_lookup(source_id)
    path = manifest_entry["source_path"]
    score = music21.converter.parse(path)

    schema_version="1.0"
    piece_id=manifest_entry["work_id"]

    '''Metadata'''
    title=score.metadata.title
    composer=score.metadata.composer
    voice_count=len(score.parts)
    duration_q=Fraction(score.duration.quarterLength)
    key = parse_key(path)
    metadata = Metadata(
        title,
        composer,
        voice_count,
        duration_q,
        key       
        )

    '''Provenance'''
    source_id = manifest_entry["source_id"]
    source_format = manifest_entry["source_format"]
    source_path = manifest_entry["source_path"]
    provenance=Provenance(
        source_id=source_id,
        source_format=source_format,
        source_path=source_path
        )

    '''Voices'''
    voices=[]
    for i, part in enumerate(score.parts):
        voices.append(Voice(id=i+1))

    '''Measures'''
    measures=[]
    score_measures = score.parts[0].getElementsByClass(music21.stream.Measure)
    for i, measure in enumerate(score_measures):
        index = i
        onset_q = measure.offset
        duration_q = measure.duration.quarterLength
        ts = measure.getContextByClass(music21.meter.TimeSignature)
        time_signature = TimeSignature(ts.numerator, ts.denominator)
        kind="regular"

        measures.append(
            Measure(
                index = index,
                onset_q = Fraction(onset_q),
                duration_q = Fraction(duration_q),
                time_signature = time_signature,
                kind = kind
                )
            )
    
    '''Events'''
    events=[]
    event_id_counter=1
    for i, part in enumerate(score.parts):
        voice = i+1
        notes_and_rests = part.recurse().notesAndRests
        for event in notes_and_rests:
            onset_q = event.getOffsetInHierarchy(part)
            duration_q = event.duration.quarterLength
            
            measure = event.getContextByClass(music21.stream.Measure)
            measure_index = measure.number-1

            if event.isChord:
                components=event.notes
            else:
                components=(event,)

            for component in components:
                if component.isRest:
                    event_type="rest"
                    pitch=None
                    tie=None
                else:
                    event_type="note"
                    tonic_step = component.pitch.step
                    if component.pitch.accidental is not None:
                        tonic_alter = int(component.pitch.accidental.alter)
                    else:
                        tonic_alter=0
                    octave = component.pitch.octave
                    pitch = Pitch(
                        step=tonic_step,
                        alter=tonic_alter,
                        octave=octave                    
                        )
                    if component.tie is not None:
                        tie = component.tie.type
                    else:
                        tie = None
                events.append(
                    Event(
                        id=f"e{event_id_counter}",
                        type = event_type,
                        voice = voice,
                        measure_index = measure_index,
                        onset_q = Fraction(onset_q),
                        duration_q = Fraction(duration_q),
                        pitch = pitch,
                        tie = tie
                        )
                    )
                event_id_counter+=1

    '''Key changes'''
    key_signatures=[] #temporary since all bach WTC fugues have no key changes


    return Score(
        schema_version=schema_version,
        piece_id=piece_id,
        metadata=metadata,
        provenance=provenance,
        voices=voices,
        measures=measures,
        events=events,
        key_signatures=key_signatures        
        )
