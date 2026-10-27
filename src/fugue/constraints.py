from fractions import Fraction

def allowed_next_tokens(
    generated_tokens: list[str],
    vocabulary: dict[str, int]
    ) -> list[str]:

    if not generated_tokens:
        return ["SCORE_START"]

    tokens = list(vocabulary)
    last_token = generated_tokens[-1]

    '''Initial tokens'''
    if last_token == "SCORE_END":
        return []

    if last_token == "SCORE_START":
        return [token for token in tokens if token.startswith("KEY_")]

    if last_token.startswith("KEY_"):
        return [token for token in tokens if token.startswith("VOICE_COUNT_")]

    if last_token.startswith("VOICE_COUNT_"):
        return ["BAR_START"]

    if last_token == "BAR_START":
        return [token for token in tokens if token.startswith("TS_")]


    '''Basic note grammar: POSITION -> VOICE -> DURATION -> TYPE -> PITCH -> TIE'''

    '''VOICE comes after POS'''
    if last_token.startswith("POS_"):

        voice_count_token = next(token for token in generated_tokens if token.startswith("VOICE_COUNT_"))
        voice_count = int(voice_count_token.removeprefix("VOICE_COUNT_"))

        bar_start = max(i for i, token in enumerate(generated_tokens) if token == "BAR_START")
        bar_tokens = generated_tokens[bar_start+1:]

        position = Fraction(last_token.removeprefix("POS_"))

        for voice_number in range(1, voice_count + 1):
            voice = f"VOICE_{voice_number}"

            if voice not in vocabulary:
                continue

            last_index = next((i for i in range(len(bar_tokens)-1, -1, -1) if bar_tokens[i]==voice), None)

            if last_index is None:
                previous_end = Fraction(0)
            else:
                previous_position = Fraction(bar_tokens[last_index - 1].removeprefix("POS_"))
                previous_duration = Fraction(bar_tokens[last_index + 1].removeprefix("DUR_"))
                previous_end = previous_position+previous_duration

            if previous_end==position:
                return [voice] #We return the first possible voice since the training data is ordered by voice
        return []



    '''DUR comes after VOICE'''
    if (last_token.startswith("VOICE_") and not last_token.startswith("VOICE_COUNT_")):
        time_signature_token = next(token for token in reversed(generated_tokens) if token.startswith("TS_"))

        _, numerator, denominator = time_signature_token.split("_")
        bar_duration = Fraction(4 * int(numerator), int(denominator))

        position = Fraction(generated_tokens[-2].removeprefix("POS_"))
        time_left_in_measure = bar_duration-position

        return [
               token for token in tokens
               if token.startswith("DUR_") 
               and (0<Fraction(token.removeprefix("DUR_"))<=time_left_in_measure)
               and (position+Fraction(token.removeprefix("DUR_")) == bar_duration or f"POS_{position+Fraction(token.removeprefix('DUR_'))}" in vocabulary)
               ]


    '''TYPE comes after DUR'''
    if last_token.startswith("DUR_"):
        allowed = [
            token
            for token in ("NOTE", "REST")
            if token in vocabulary
            ]
        voice = generated_tokens[-2]

        previous_tokens = generated_tokens[:-3]

        last_index = next((i for i in range(len(previous_tokens)-1,-1,-1) if previous_tokens[i] == voice), None)

        if last_index is not None:
            previous_type = previous_tokens[last_index+2]

            if previous_type == "NOTE":
                previous_tie = previous_tokens[last_index+4]

                if previous_tie in {"TIE_START", "TIE_CONTINUE"}:
                    allowed = [token for token in allowed if token != "REST"]
        return allowed

    '''PITCH comes after NOTE'''
    if last_token == "NOTE":

        voice = generated_tokens[-3]

        previous_tokens = generated_tokens[:-3]

        last_index = next((i for i in range(len(previous_tokens)-1,-1,-1) if previous_tokens[i] == voice), None)

        if last_index is not None:
            previous_type = previous_tokens[last_index+2]

            if previous_type == "NOTE":
                previous_tie = previous_tokens[last_index+4]
                previous_pitch = previous_tokens[last_index+3]

                if previous_tie in {"TIE_START", "TIE_CONTINUE"}:
                    return [previous_pitch]
        
        allowed = [token for token in vocabulary if token.startswith("PITCH_")]
        return allowed

    '''TIE comes after PITCH'''
    if last_token.startswith("PITCH_"):

        voice = generated_tokens[-4]

        previous_tokens = generated_tokens[:-4]

        last_index = next((i for i in range(len(previous_tokens)-1,-1,-1) if previous_tokens[i] == voice), None)

        if last_index is not None:
            previous_type = previous_tokens[last_index+2]

            if previous_type == "NOTE":
                previous_tie = previous_tokens[last_index+4]

                if previous_tie in {"TIE_START", "TIE_CONTINUE"}:
                    return ["TIE_CONTINUE","TIE_STOP"]
                
        return ["TIE_START", "TIE_NONE"]
     
    '''POS comes after TS'''
    if last_token.startswith("TS_"):
        return ["POS_0"]

    '''What comes after REST or TIE'''
    if last_token == "REST" or last_token.startswith("TIE_"):

        voice_count_token = next(token for token in generated_tokens if token.startswith("VOICE_COUNT_"))
        voice_count = int(voice_count_token.removeprefix("VOICE_COUNT_"))

        voice_ends = {
            i: Fraction(0) for i in range(1, voice_count + 1)
            }

        bar_start = max(i for i, token in enumerate(generated_tokens) if token == "BAR_START")
        bar_tokens = generated_tokens[bar_start+1:]

        for voice_number in range(1, voice_count + 1):
            voice = f"VOICE_{voice_number}"

            if voice not in vocabulary:
                continue

            last_index = next((i for i in range(len(bar_tokens)-1, -1, -1) if bar_tokens[i]==voice), None)

            if last_index is not None:

                previous_position = Fraction(bar_tokens[last_index - 1].removeprefix("POS_"))
                previous_duration = Fraction(bar_tokens[last_index + 1].removeprefix("DUR_"))
                previous_end = previous_position+previous_duration
                voice_ends[voice_number]=previous_end


        time_signature_token = next(token for token in reversed(generated_tokens) if token.startswith("TS_"))

        _, numerator, denominator = time_signature_token.split("_")
        bar_duration = Fraction(4 * int(numerator), int(denominator))

        if all(end == bar_duration for end in voice_ends.values()):
            return ["BAR_END"]


        next_position = min(list(voice_ends.values()))
        position_token = f"POS_{next_position}"
        
        if position_token not in vocabulary:
            raise ValueError(f"Required position token not in vocabulary: {position_token}")

        return [position_token]


    '''What happens at end of bar'''
    if last_token == "BAR_END":

        voice_count_token = next(token for token in generated_tokens if token.startswith("VOICE_COUNT_"))
        voice_count = int(voice_count_token.removeprefix("VOICE_COUNT_"))

        voice_ties = {
            i: None for i in range(1, voice_count + 1)
            }

        bar_start = max(i for i, token in enumerate(generated_tokens) if token == "BAR_START")
        bar_tokens = generated_tokens[bar_start+1:]

        for voice_number in range(1, voice_count + 1):
            voice = f"VOICE_{voice_number}"

            if voice not in vocabulary:
                continue

            last_index = next((i for i in range(len(bar_tokens)-1, -1, -1) if bar_tokens[i]==voice), None)

            if last_index is not None:
                if bar_tokens[last_index+2]=="NOTE":
                    if bar_tokens[last_index+4] not in ("TIE_NONE", "TIE_STOP"):
                        voice_ties[voice_number]="TIE"
        if all(tie is None for tie in voice_ties.values()):
            return ["BAR_START", "SCORE_END"]
        else:
            return ["BAR_START"]

    raise ValueError(f"Unexpected token while applying grammar: {last_token}")

   