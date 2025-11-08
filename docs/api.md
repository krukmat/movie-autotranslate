# API Notes

## Job Management
- `GET /v1/jobs?page=1&pageSize=20` → returns `items`, `total`, `page`, `pageSize`; each item includes `stageHistory`, `logsKey`, presets, etc.
- `POST /v1/jobs/{jobId}/retry` → body `{ "resumeFrom": "TTS" }` (optional). Resets the job, requeues the pipeline from the chosen stage.
- `DELETE /v1/jobs/{jobId}` → marks the job as `CANCELLED`. Currently this stops scheduling further stages but does not preempt already running Celery tasks; those will finish but their output is ignored.

## Resume Semantics
- Use `/v1/jobs/{id}` to inspect `stageHistory` and decide an appropriate `resumeFrom` stage.
- Stages upstream from `resumeFrom` are reused when their artifacts exist; deleting the relevant files (e.g., `data/proc/<asset>/tts/<lang>`) forces regeneration.

## Schema Regeneration
- Run `python scripts/generate_openapi.py` whenever routes change; commit both `docs/openapi.json` and `docs/openapi.yaml` so clients can regenerate SDKs.
- Frontend/mobile clients should watch for the `logsKey` field to fetch detailed logs from MinIO.
