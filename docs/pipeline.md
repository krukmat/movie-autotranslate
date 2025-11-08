# Pipeline Stages & Resume Flow

The dubbing worker executes deterministic stages in order:

1. **ASR** (`JobStage.ASR`) — Whisper-based transcription writes `asr/segments_src.json`.
2. **TRANSLATE** — LibreTranslate/Marian outputs `translations/segments_tgt.<lang>.json`.
3. **TTS** — Piper synthesizes per-segment WAVs into `tts/<lang>/seg_*.wav`.
4. **ALIGN/MIX** — Audio engineering combines TTS segments (and optional Demucs backing track) into `mix/<lang>/dubbed.wav`.
5. **PACKAGE** — Publishes HLS/audio assets to MinIO and updates `storage_keys`.

Each stage records events in the job’s `stageHistory` field (`status=success/skipped/failed` plus per-language details). Logs are captured per job and uploaded to MinIO (`logsKey`) after finalization.

## Resume & Reuse
- When (re)creating a job you can pass `resumeFrom` (`ASR`, `TRANSLATE`, `TTS`, `ALIGN/MIX`, `PACKAGE`). Earlier stages are **skipped automatically** if their artifacts are still present; otherwise they rerun to guarantee consistency.
- Artifacts are detected on disk (`data/proc/<assetId>/...`). Deleting a file forces the pipeline to regenerate that stage even if `resumeFrom` is later.
- If a stage fails, `stageHistory` captures the error and the pipeline stops. Retrying with `resumeFrom` set to the failed stage (or later) will reuse preceding stages.

## Monitoring
- Use `/v1/jobs/{id}` to inspect `stageHistory` and `logsKey`.
- Worker metrics (`job_stage_in_progress`, `job_stage_failures_total`, `job_stage_duration_seconds`) reflect the per-stage execution described above.
