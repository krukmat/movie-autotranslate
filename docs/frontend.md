# Frontend Notes

## Upload Flow
- Users can select multiple target languages via the checkboxes on `/` and choose a default voice preset (neutral, female_bright, male_deep, etc.). The form validates that a file and at least one language are provided before creating a job.
- Preset selection maps to the backend `presets.default` field; extend the UI if you expose per-speaker controls later.

## Job Detail View
- `/jobs/:id` now shows a stage history table (status per pipeline stage) and exposes the `logsKey` so ops can fetch JSONL logs directly from storage.
- When the job finishes successfully, the “Open player” link remains available.

## Playback
- `/watch/:assetId` surfaces any published audio tracks (`public_<lang>`) so users can switch between language-specific outputs when available.
- The HLS player falls back to the master manifest when no alternates are available.
