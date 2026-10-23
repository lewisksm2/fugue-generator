from fractions import Fraction
import json
from pathlib import Path
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
from fugue.parse import(
    parse_humdrum_kern
    )
from fugue.ingest import(
    _read_manifest
    )




tie_dict = {
    "start" : "START",
    "continue" : "CONTINUE",
    "stop" : "STOP",
    None : "NONE"    
    }

r_tie_dict = {
    "START" : "start",
    "CONTINUE" : "continue",
    "STOP" : "stop",
    "NONE" : None
}

def score_to_tokens(score: Score) -> list[str]:
    tokens=[]

    '''Beginning of piece'''
    tokens.append("SCORE_START")

    '''Key signature'''
    ks = score.metadata.key
    tokens.append(f"KEY_{ks.tonic_step}({str(ks.tonic_alter)})_{ks.mode.upper()}") 

    '''Number of voices'''
    tokens.append(f"VOICE_COUNT_{score.metadata.voice_count}")


    events = sorted(
    score.events,
    key=lambda event: (event.onset_q, event.voice, event.id),
        )
    event_index=0
    number_of_events=len(events)
    '''Loop over measures'''
    for measure in score.measures:
        tokens.append("BAR_START")


        '''Time signature'''
        ts = measure.time_signature
        tokens.append(f"TS_{ts.numerator}_{ts.denominator}")


        #Later version can allow changes in key here.
 
        '''Loop over events in measure'''
        while event_index < len(events) and events[event_index].onset_q < measure.onset_q+measure.duration_q:

            event = events[event_index]
            
            rel_position_q = event.onset_q - measure.onset_q

            tokens.append(f"POS_{str(rel_position_q)}")
            tokens.append(f"VOICE_{str(event.voice)}")
            tokens.append(f"DUR_{str(event.duration_q)}")
            tokens.append(event.type.upper())
            if event.type == "note":
                tokens.append(f"PITCH_{event.pitch.step}({str(event.pitch.alter)}){str(event.pitch.octave)}")
                tokens.append(f"TIE_{tie_dict[event.tie]}")
           
            event_index+=1
            if event_index>=number_of_events:
                break

        tokens.append("BAR_END")


    '''End of piece'''
    tokens.append("SCORE_END")

    return tokens

def tokens_to_score(tokens: list[str]) -> Score:
    schema_version="1.0"
    piece_id="tokens"

    time_signatures=[token for token in tokens if token.startswith('TS')]
    duration=0
    for ts in time_signatures:
        _,numerator,denominator = ts.split("_")
        duration+= Fraction(numerator)*Fraction(4)/Fraction(denominator)

    tonic_alter=0
    if tokens[1][6]=="-":
        tonic_alter=int(tokens[1][6:8])
    else:
        tonic_alter=int(tokens[1][6])
    metadata = Metadata(
        title="tokens",
        composer="tokens",
        voice_count=int(tokens[2][12]),
        duration_q=duration,
        key=Key(
            tonic_step=tokens[1][4],
            tonic_alter=tonic_alter,
            mode=tokens[1][-5:].lower()
            )
    )
    provenance = Provenance(
        source_id="tokens",
        source_format="synthetic",
        source_path=None
        )
    voices=[]
    for i in range(metadata.voice_count):
        voices.append(Voice(i+1))
    
    measures=[]
    events=[]
    measure_index=0
    event_index=1
    current_pos=Fraction(0)
    measure_ts=TimeSignature(4,4)
    for i,token in enumerate(tokens):
        if token[0:2]=="TS":
            _,numerator,denominator = token.split("_")
            measure_ts = TimeSignature(int(numerator), int(denominator))
        measure_duration = Fraction(measure_ts.numerator)*Fraction(4)/Fraction(measure_ts.denominator)
        if token=="BAR_END":
            measures.append(
                Measure(
                    index=measure_index,
                    onset_q=current_pos,
                    duration_q=measure_duration,
                    time_signature=measure_ts,
                    kind="regular"
                    )
                )
            measure_index+=1
            current_pos+=measure_duration

        if token[0:3]=="POS":
            e_id=f"e{event_index}"
            e_type=""
            if tokens[i+3]=="REST":
                e_type="rest"
            else:
                e_type="note"
            e_voice = int(tokens[i+1][6])
            e_onset=current_pos+Fraction(token[4:])
            e_duration = Fraction(tokens[i+2][4:])
            e_pitch=None
            e_tie=None
            if e_type=="rest":
                e_pitch=None
                e_tie=None
            else:
                p_token=tokens[i+4]
                step=p_token[6]
                alter=0
                if p_token[8]=="-":
                    alter=int(p_token[8:10])
                else:
                    alter=int(p_token[8])
                
                octave=int(p_token[-1])
                e_pitch=Pitch(
                    step,alter,octave
                    )
                e_tie=r_tie_dict[tokens[i+5][4:]]
            events.append(
                Event(
                    e_id,
                    e_type,
                    e_voice,
                    measure_index,
                    e_onset,
                    e_duration,
                    e_pitch,
                    e_tie
                    )
                )
            event_index+=1
    key_signatures=[]

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

def build_vocabulary() -> dict[str, int]:
    manifest = _read_manifest(Path("data/manifest.jsonl"))

    scores=[]
    for entry in manifest:
        if entry["work_id"] not in ["wtc1f11", "wtc1f20"]:
            print(entry["work_id"])
            scores.append(parse_humdrum_kern(entry["source_id"]))

    token_sequences = [
        score_to_tokens(score)
        for score in scores
        ]

    unique_tokens = {
        token
        for sequence in token_sequences
        for token in sequence
        }

    vocabulary = ["PAD"] + sorted(unique_tokens - {"PAD"})

    return {
        token: index
        for index, token in enumerate(vocabulary)
        }

def tokens_to_ids(tokens: list[str], vocabulary: dict[str,int]) -> list[int]: 
    return [vocabulary[token] for token in tokens]

def ids_to_tokens(ids: list[int], vocabulary: dict[str,int]) -> list[str]:
    reverse = {
        index: token
        for token, index in vocabulary.items()        
        }
    return [reverse[index] for index in ids]

def save_vocabulary(vocabulary: dict[str, int], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(vocabulary, indent=2, ensure_ascii=False)+"\n",
        encoding="utf-8"
        )

def load_vocabulary(path: Path) -> dict[str,int]:
    return json.loads(path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    path = Path("data/derived/tokens_v1/vocabulary.json")
    vocabulary = build_vocabulary()
    save_vocabulary(vocabulary, path)
