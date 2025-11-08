# ML Prompt — Speaker Diarization (Optional)

## Objective
Detect who is speaking when, to assign consistent voices per speaker.

## Steps
1. Run diarization (e.g., pyannote) over source audio → segments with `speaker` labels.
2. Map diarization segments to ASR segments (overlap-based assignment).
3. Produce `speakers.json`: { S0: {gender?: "M|F", notes?: "..."} ... }.
4. Generate default voice map: S0→male_deep, S1→female_bright, S2→neutral.

## Acceptance
- No segment left without a speakerId when enabled.
- Simple heuristics to keep #speakers <= N_max (configurable) by merging small speakers.
