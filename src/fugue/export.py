from fugue.schema import Score
import music21

def score_to_music21(score: Score) -> music21.stream.Score:

    output = music21.stream.Score()

    '''Metadata'''
    output.metadata = music21.metadata.Metadata()
    output.metadata.title = score.metadata.title
    output.metadata.composer = score.metadata.composer

    measures = sorted(score.measures, key=lambda measure: measure.index)

    for voice in sorted(score.voices, key=lambda voice: voice.id):
        part = music21.stream.Part(id=f"voice_{voice.id}")
        part.partName = f"Voice {voice.id}"

        measure_lookup ={}
        previous_time_signature = None

        for measure in measures:
            output_measure = music21.stream.Measure(number = measure.index+1)
            ts = measure.time_signature
            time_signature = (ts.numerator, ts.denominator)

            if time_signature != previous_time_signature:
                output_measure.timeSignature = music21.meter.TimeSignature(f"{ts.numerator}/{ts.denominator}")
                previous_time_signature = time_signature
            part.insert(measure.onset_q, output_measure)
            measure_lookup[measure.index] = output_measure

        first_measure = measure_lookup[measures[0].index]
        key = score.metadata.key

        if key is not None:
            tonic = music21.pitch.Pitch()
            tonic.step = key.tonic_step
            tonic.accidental = music21.pitch.Accidental(key.tonic_alter)

            first_measure.insert(0, music21.key.Key(tonic, key.mode))

        voice_events = sorted(
            (
                event for event in score.events
                if event.voice == voice.id
                ),
                key = lambda event: (event.onset_q, event.id)
            )

        source_measures = {
            measure.index: measure
            for measure in measures
            }

        for event in voice_events:

            if event.type == "rest":
                item = music21.note.Rest()

            elif event.type == "note":
                pitch = music21.pitch.Pitch()
                pitch.step = event.pitch.step
                pitch.octave = event.pitch.octave
                pitch.accidental = music21.pitch.Accidental(event.pitch.alter)

                item = music21.note.Note(pitch)

                if event.tie is not None:
                    item.tie = music21.tie.Tie(event.tie)

            item.duration.quarterLength = event.duration_q

            source_measure = source_measures[event.measure_index]
            output_measure = measure_lookup[event.measure_index]

            relative_position = event.onset_q - source_measure.onset_q

            output_measure.insert(relative_position,item)

        first_measure.insert(0, music21.clef.bestClef(part, recurse=True))
        output.insert(0,part)

    return output


def export_musicxml(score: Score, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    music21_score = score_to_music21(score)
    music21_score.write("musicxml", fp=str(path))