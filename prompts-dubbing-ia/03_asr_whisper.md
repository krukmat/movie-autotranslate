# ML Prompt — ASR (Whisper via faster-whisper)

## Objective
Implement ASR that produces timestamped segments from source audio.
- Default: `faster-whisper` with `small` model quantized int8; support env to switch model size.
- Input: WAV/MP3 path or S3 key.
- Output: JSON list of segments: `{idx, t0, t1, text, lang, speakerId?}`

## Steps
1. Load model once per worker; warm cache.
2. Run VAD (optional) to pre-trim long silences.
3. Transcribe -> collect segments with precise start/end.
4. If diarization is enabled: map each segment to `speakerId` (S0,S1,...) using diarization JSON.
5. Persist as `segments_src.json` to storage.

## Acceptance
- For a 5–10 min sample, RTF <= 4x on CPU VM.
- Language auto-detection matches the source language correctly.
- Segments are contiguous, non-overlapping, and cover all voiced regions.
