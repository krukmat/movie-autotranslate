# ML Prompt — TTS (Piper default; Coqui XTTS-v2 optional)

## Objective
Generate per-segment speech in the target language with chosen voice preset or clone.

## Presets
- `male_deep`, `female_bright`, `elderly_male`, `elderly_female`, `neutral`

## Steps
1. Load engine by preset:
   - Piper (CPU/offline) with selected voice ID per language.
   - XTTS-v2 (requires GPU) when `ENGINE=coqui` or for clone mode.
2. For each segment, synthesize WAV at 48kHz mono.
3. Store as `tts/{lang}/seg_{idx}.wav`.

## Auto-Tuning
- **Duration fitting**: compute `tempo = clamp((t1 - t0)/tts_len, 0.90, 1.10)`; apply time-stretch (`atempo`).
- **Styling** (preset): small pitch/EQ changes (e.g., elderly = slight pitch down + slower tempo).
- **Loudness**: normalize whole track to ~–16 LUFS using `loudnorm` aggregator after concatenation.

## Acceptance
- Segment WAVs concatenate without clicks; final track duration within ±0.5% of original voiced duration.
